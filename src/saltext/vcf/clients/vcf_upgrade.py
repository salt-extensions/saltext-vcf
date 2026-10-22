"""SDDC Manager upgrade API payloads, discovery, prechecks and monitoring."""

import logging
import re
import time

from saltext.vcf.utils.vcf_upgrade_transport import CommandExecutionError
from saltext.vcf.utils.vcf_upgrade_transport import SddcConnectionError
from saltext.vcf.utils.vcf_upgrade_transport import SddcHttpError
from saltext.vcf.utils.vcf_upgrade_transport import SddcManagerClient
from saltext.vcf.utils.vcf_upgrade_transport import boolean
from saltext.vcf.utils.vcf_upgrade_transport import poll_settings

SUCCESS_UPGRADE = {"COMPLETED_WITH_SUCCESS", "SUCCESSFUL", "SUCCESS"}
FAIL_UPGRADE = {
    "FAILED",
    "COMPLETED_WITH_FAILURE",
    "CANCELLED",
    "ERROR",
    "COMPLETED_WITH_WARNING",
    "COMPLETED_WITH_ERRORS",
    "SKIPPED",
}
BUNDLE_TERMINAL = {"SUCCESSFUL", "FAILED", "CANCELLED"}


COMPONENTS = {"SDDC_MANAGER", "NSX_T_MANAGER", "VCENTER", "HOST"}


def _version(value):
    text = str(value or "").split(" ", 1)[0]
    match = re.fullmatch(r"(\d+(?:\.\d+)*)(?:-(\d+(?:\.\d+)*))?", text)
    if not match:
        raise CommandExecutionError(f"Invalid version: {value!r}")
    parts = tuple(int(x) for x in match[1].split("."))
    if len(parts) > 5 or (len(parts) == 5 and match[2]):
        raise CommandExecutionError("Unsupported version layout")
    build = str(parts[4]) if len(parts) == 5 else match[2]
    if build and "." in build:
        # vLCM image notation is release-0.0.build.
        prefix, _, build = build.rpartition(".")
        if prefix != "0.0":
            raise CommandExecutionError("Unsupported image build layout")
    return tuple((list(parts[:4]) + [0] * 4)[:4]), build


def _triplet(value):
    return _version(value)[0][:3]


def _version_match(target, bundle_version):
    if not target:
        return True
    target_parts, target_build = _version(target)
    bundle_parts, bundle_build = _version(bundle_version)
    return target_parts == bundle_parts and (target_build is None or target_build == bundle_build)


def _component(value):
    value = str(value).upper()
    if value not in COMPONENTS:
        raise CommandExecutionError(f"Unsupported component_type: {value}")
    return value


def _id(value, name):
    if not value or not re.fullmatch(r"[A-Za-z0-9_.:-]+", str(value)):
        raise CommandExecutionError(f"A valid {name} is required")
    return str(value)


class VcfUpgradeProvider:
    def __init__(
        self,
        host,
        username,
        password,
        protocol="https",
        port=443,
        verify_ssl=True,
        timeout=60,
        logger=None,
    ):
        self.log = logger or logging.getLogger(__name__)
        self.client = SddcManagerClient(
            host, username, password, protocol, port, verify_ssl, timeout, self.log
        )

    def list_target_versions(
        self,
        component_type="SDDC_MANAGER",
        domain_id=None,
        current_version=None,
        min_bump="MAJOR_OR_MINOR",
    ):
        component_type = _component(component_type)
        if min_bump not in {"MAJOR_OR_MINOR", "ANY"}:
            raise CommandExecutionError("min_bump must be MAJOR_OR_MINOR or ANY")
        if not domain_id:
            domain_id = self.management_domain_id()
        current = current_version or self.current_domain_version(domain_id)
        releases = self.client.elements("/v1/releases", params={"includeOnlyCompatible": "true"})
        cur = tuple(
            int(x) if str(x).isdigit() else 0
            for x in (str(current).split("-")[0].split(".") + ["0"] * 4)[:4]
        )
        out = set()
        for r in releases:
            v = r.get("version")
            if not v or not any(c.get("name") == component_type for c in r.get("bom", [])):
                continue
            vt = tuple(
                int(x) if str(x).isdigit() else 0
                for x in (str(v).split("-")[0].split(".") + ["0"] * 4)[:4]
            )
            if vt <= cur:
                continue
            if min_bump == "MAJOR_OR_MINOR" and vt[:2] == cur[:2]:
                continue
            out.add(v)
        return sorted(
            out,
            key=lambda v: tuple(
                int(x) if x.isdigit() else 0 for x in (v.split("-")[0].split(".") + ["0"] * 4)[:4]
            ),
            reverse=True,
        )

    def list_bundle_builds(self, release_version, component_type="SDDC_MANAGER"):
        component_type = _component(component_type)
        bundles = self.client.elements("/v1/bundles")
        matches = {}
        for b in bundles:
            if component_type not in [c.get("type") for c in b.get("components", [])]:
                continue
            if not _version_match(release_version, b.get("version")):
                continue
            matches[b.get("version")] = b

        def build(v):
            m = re.search(r"-(\d+)", str(v))
            return int(m.group(1)) if m else 0

        result = []
        for v in sorted(matches, key=build, reverse=True):
            d = str(matches[v].get("releasedDate") or "")[:10]
            result.append(f"{v} (released {d})" if d else v)
        return result

    def find_bundle(self, component_type, target_version=None, status=None):
        component_type = _component(component_type)
        bundles = self.client.elements("/v1/bundles")
        matches = []
        for b in bundles:
            if component_type not in [c.get("type") for c in b.get("components", [])]:
                continue
            if not _version_match(target_version, b.get("version")):
                continue
            matches.append(b)
        versions = {b.get("version") for b in matches}
        if len(versions) > 1:
            raise CommandExecutionError(
                f"Multiple {component_type} bundle versions match {target_version}: {sorted(versions)}; "
                "pass an exact build such as 9.2.0-25522192"
            )
        if status is not None:
            matches = [b for b in matches if b.get("downloadStatus") == status]
        ids = {b.get("id") for b in matches}
        if len(ids) > 1:
            raise CommandExecutionError(
                "Multiple bundle IDs match; resolve the catalog ambiguity first"
            )
        return matches[0] if matches else None

    def ensure_bundle_download(self, component_type, target_version=None):
        existing = self.find_bundle(component_type, target_version, "SUCCESSFUL")
        if existing:
            return {
                "changed": False,
                "bundleId": existing["id"],
                "version": existing.get("version"),
                "downloadStatus": "SUCCESSFUL",
                "alreadyDownloaded": True,
            }
        b = self.find_bundle(component_type, target_version, None)
        if not b:
            raise CommandExecutionError(
                f"No {component_type} bundle found for target {target_version}"
            )
        if b.get("downloadStatus") in {"IN_PROGRESS", "SCHEDULED"}:
            return {
                "changed": False,
                "bundleId": b["id"],
                "version": b.get("version"),
                "downloadStatus": b["downloadStatus"],
                "alreadyDownloaded": False,
            }
        resp = self.client.patch(
            f"/v1/bundles/{b['id']}", {"bundleDownloadSpec": {"downloadNow": True}}
        )
        return {
            "changed": True,
            "bundleId": b["id"],
            "version": b.get("version"),
            "taskId": resp.get("id"),
            "downloadStatus": b.get("downloadStatus"),
            "alreadyDownloaded": False,
        }

    def wait_bundle(self, bundle_id, timeout=14400, interval=60):
        deadline, interval = poll_settings(timeout, interval)
        last = None
        while time.monotonic() < deadline:
            last = self.client.get(f"/v1/bundles/{_id(bundle_id, 'bundle_id')}")
            st = str(last.get("downloadStatus", "UNKNOWN")).upper()
            self.log.info("VCF bundle %s downloadStatus=%s", bundle_id, st)
            if st == "SUCCESSFUL":
                return {"bundleId": bundle_id, "downloadStatus": st, "changed": True}
            if st in {"FAILED", "CANCELLED"}:
                raise CommandExecutionError(f"Bundle {bundle_id} download ended with {st}")
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
        raise CommandExecutionError(f"Timed out waiting for bundle {bundle_id}")

    def management_domain_id(self):
        domains = self.client.elements("/v1/domains")
        for d in domains:
            if str(d.get("type", "")).upper() == "MANAGEMENT":
                return d.get("id")
        raise CommandExecutionError("Could not determine management domain id")

    def current_domain_version(self, domain_id):
        releases = self.client.elements("/v1/releases", {"domainId": _id(domain_id, "domain_id")})
        versions = {r.get("version") for r in releases if r.get("version")}
        if len(versions) != 1:
            raise CommandExecutionError("Could not resolve a unique current domain release")
        return versions.pop()

    def plan(self, component_type="SDDC_MANAGER", target_version=None, domain_id=None):
        domain_id = domain_id or self.management_domain_id()
        b = self.find_bundle(component_type, target_version, "SUCCESSFUL")
        if not b:
            raise CommandExecutionError("Target bundle is not downloaded successfully")
        return {
            "domainId": domain_id,
            "bundleId": b["id"],
            "targetVersion": b.get("version"),
            "releasedDate": b.get("releasedDate"),
        }

    def _nsxt_fqdn(self, domain_id):
        d = self.client.get(f"/v1/domains/{domain_id}")
        return (d.get("nsxtCluster") or {}).get("vipFqdn")

    def build_upgrade_payload(
        self,
        domain_id,
        bundle_id,
        target_version,
        component_type="SDDC_MANAGER",
        draft_mode=None,
        schedule_for_later=False,
        scheduled_timestamp=None,
        cluster_id=None,
        personality_id=None,
        nsx_mp_upgrade=True,
        nsx_datapath_appliance_upgrade=False,
        nsx_edge_only_upgrade=False,
        nsx_host_clusters_upgrade_parallel=False,
        nsx_edge_clusters_upgrade_parallel=False,
        vcenter_upgrade_mechanism="InPlace",
        vcenter_appliance_size="MEDIUM",
        vcenter_appliance_storage_size="REGULAR",
        vcenter_network_mode="AUTOMATIC",
        parallel_upgrade=True,
        esx_enable_quickboot=True,
        esx_enable_quick_patch=True,
        esx_evacuate_offline_vms=True,
        esx_pre_remediation_power_action="DO_NOT_CHANGE_VMS_POWER_STATE",
        esx_silence_vsan_hcl_during_upgrade=True,
        esx_upgrade_failure_action="RETRY",
        esx_upgrade_failure_retry_count=3,
        esx_upgrade_failure_retry_delay=300,
        esx_quick_patch_mode="AUTO",
    ):
        component_type = _component(component_type)
        _id(domain_id, "domain_id")
        _id(bundle_id, "bundle_id")
        if not target_version:
            raise CommandExecutionError("target_version is required")
        _version(target_version)
        schedule_for_later = boolean(schedule_for_later, "schedule_for_later")
        if draft_mode is None:
            draft_mode = component_type != "SDDC_MANAGER"
        draft_mode = boolean(draft_mode, "draft_mode")
        if component_type == "SDDC_MANAGER" and draft_mode:
            raise CommandExecutionError("SDDC_MANAGER does not support draft mode")
        if component_type != "SDDC_MANAGER" and not draft_mode:
            raise CommandExecutionError("NSX, VCENTER and HOST require draft mode and prechecks")
        if schedule_for_later and not scheduled_timestamp:
            raise CommandExecutionError(
                "scheduled_timestamp is required when schedule_for_later=true"
            )
        resource_type = "CLUSTER" if component_type == "HOST" else "DOMAIN"
        if component_type == "HOST" and (not cluster_id or not personality_id):
            raise CommandExecutionError("HOST upgrade requires cluster_id and personality_id")

        if component_type == "HOST":
            _id(cluster_id, "cluster_id")
            _id(personality_id, "personality_id")
            cluster = self.client.get(f"/v1/clusters/{cluster_id}")
            if (cluster.get("domain") or {}).get("id") != domain_id:
                raise CommandExecutionError("HOST cluster does not belong to the selected domain")
        if component_type == "VCENTER":
            if vcenter_upgrade_mechanism not in {"InPlace", "ReducedDowntimeMigration"}:
                raise CommandExecutionError("Unsupported vcenter_upgrade_mechanism")
            if vcenter_network_mode != "AUTOMATIC":
                raise CommandExecutionError("Only AUTOMATIC temporary networking is supported")
        if component_type == "NSX_T_MANAGER" and not (
            boolean(nsx_mp_upgrade) or boolean(nsx_datapath_appliance_upgrade)
        ):
            raise CommandExecutionError("At least one NSX upgrade phase must be enabled")
        spec = {"resourceId": cluster_id if component_type == "HOST" else domain_id}
        if component_type == "HOST":
            spec.update(
                {
                    "type": "CLUSTER",
                    "personalitySpec": {"personalityId": personality_id},
                    "esxUpgradeOptionsSpec": {
                        "enableQuickboot": boolean(esx_enable_quickboot),
                        "enableQuickPatch": boolean(esx_enable_quick_patch),
                        "evacuateOfflineVms": boolean(esx_evacuate_offline_vms),
                        "preRemediationPowerAction": esx_pre_remediation_power_action,
                        "silenceVsanHclDuringUpgrade": boolean(esx_silence_vsan_hcl_during_upgrade),
                        "esxUpgradeFailureAction": {
                            "action": esx_upgrade_failure_action,
                            "retryCount": int(esx_upgrade_failure_retry_count),
                            "retryDelay": int(esx_upgrade_failure_retry_delay),
                        },
                        "quickPatchOptions": {"quickPatchMode": esx_quick_patch_mode},
                    },
                }
            )
        elif component_type == "SDDC_MANAGER":
            spec["toVersion"] = str(target_version).split(" ", 1)[0]

        if draft_mode:
            spec["upgradeNow"] = False
        else:
            spec["upgradeNow"] = not schedule_for_later
            if schedule_for_later:
                spec["scheduledTimestamp"] = scheduled_timestamp

        payload = {
            "bundleId": bundle_id,
            "draftMode": boolean(draft_mode),
            "resourceType": resource_type,
            "resourceUpgradeSpecs": [spec],
        }
        if component_type == "HOST":
            payload["parallelUpgrade"] = boolean(parallel_upgrade)
        elif component_type == "NSX_T_MANAGER":
            fqdn = self._nsxt_fqdn(domain_id)
            if not fqdn:
                raise CommandExecutionError(f"No nsxtCluster.vipFqdn found for domain {domain_id}")
            payload["nsxtUpgradeUserInputSpecs"] = [
                {
                    "nsxtId": fqdn,
                    "nsxtUpgradeOptions": {
                        "isMpUpgrade": boolean(nsx_mp_upgrade),
                        "isDatapathApplianceUpgrade": boolean(nsx_datapath_appliance_upgrade),
                        "isEdgeOnlyUpgrade": boolean(nsx_edge_only_upgrade),
                        "isHostClustersUpgradeParallel": boolean(
                            nsx_host_clusters_upgrade_parallel
                        ),
                        "isEdgeClustersUpgradeParallel": boolean(
                            nsx_edge_clusters_upgrade_parallel
                        ),
                    },
                }
            ]
        elif component_type == "VCENTER":
            v = {"resourceId": domain_id, "upgradeMechanism": vcenter_upgrade_mechanism}
            if vcenter_upgrade_mechanism == "ReducedDowntimeMigration":
                v["targetVcenterAppliance"] = {
                    "applianceSize": vcenter_appliance_size,
                    "storageSize": vcenter_appliance_storage_size,
                }
                v["temporaryNetwork"] = {"networkMode": vcenter_network_mode}
            payload["vcenterUpgradeUserInputSpecs"] = [v]

        return payload

    def create_upgrade(
        self, domain_id, bundle_id, target_version, component_type="SDDC_MANAGER", **options
    ):
        """Create from the same validated payload used by read-only preflight."""
        payload = self.build_upgrade_payload(
            domain_id, bundle_id, target_version, component_type, **options
        )
        draft_mode = payload["draftMode"]
        resp = self.client.post("/v1/upgrades", payload)
        task_id = resp.get("id")
        upgrade_id = None
        for r in resp.get("resources", []) if isinstance(resp, dict) else []:
            if r.get("type") == "UPGRADE_ID":
                upgrade_id = r.get("resourceId")
                break
        upgrade_id = upgrade_id or task_id
        if not upgrade_id:
            raise CommandExecutionError("Upgrade creation returned no usable id")
        return {
            "changed": True,
            "upgradeId": upgrade_id,
            "taskId": task_id,
            "draftModeUsed": boolean(draft_mode),
            "domainId": domain_id,
            "bundleId": bundle_id,
            "targetVersion": target_version,
            "response": resp,
        }

    def execute_upgrade(self, upgrade_id, schedule_for_later=False, scheduled_timestamp=None):
        _id(upgrade_id, "upgrade_id")
        schedule_for_later = boolean(schedule_for_later, "schedule_for_later")
        status = str(self.upgrade_status(upgrade_id).get("status", "")).upper()
        if status in SUCCESS_UPGRADE | {"SCHEDULED", "IN_PROGRESS"}:
            return {"changed": False, "upgradeStatus": status}
        if status != "DRAFT":
            raise CommandExecutionError(
                f"Upgrade {upgrade_id} cannot execute from {status or 'UNKNOWN'}"
            )
        if schedule_for_later:
            if not scheduled_timestamp:
                raise CommandExecutionError("scheduled_timestamp is required")
            body = {"scheduledTimestamp": scheduled_timestamp, "upgradeNow": False}
        else:
            body = {"upgradeNow": True}
        return {"changed": True, "response": self.client.patch(f"/v1/upgrades/{upgrade_id}", body)}

    def wait_draft(self, upgrade_id, timeout=7200, interval=60):
        deadline, interval = poll_settings(timeout, interval)
        while time.monotonic() < deadline:
            status = str(self.upgrade_status(upgrade_id).get("status", "")).upper()
            if status == "DRAFT":
                return
            if status not in {"PENDING", "IN_PROGRESS"}:
                raise CommandExecutionError(f"Expected DRAFT upgrade; found {status or 'UNKNOWN'}")
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
        raise CommandExecutionError("Timed out waiting for draft creation")

    def upgrade_status(self, upgrade_id):
        return self.client.get(f"/v1/upgrades/{_id(upgrade_id, 'upgrade_id')}")

    def _component_to_version(self, bundle_id, component_type):
        b = self.client.get(f"/v1/bundles/{_id(bundle_id, 'bundle_id')}")
        for c in b.get("components", []):
            if c.get("type") == component_type:
                if c.get("toVersion"):
                    return c["toVersion"]
        raise CommandExecutionError(
            f"Bundle {bundle_id} has no {component_type} component target version"
        )

    def _precheck_resource_id(self, domain_id, component_type):
        if component_type == "HOST":
            return None
        d = self.client.get(f"/v1/domains/{domain_id}")
        if component_type == "NSX_T_MANAGER":
            rid = (d.get("nsxtCluster") or {}).get("vipFqdn")
        elif component_type == "VCENTER":
            vcs = d.get("vcenters") or []
            rid = vcs[0].get("fqdn") if vcs else None
        else:
            raise CommandExecutionError(
                f"Separate check-set precheck is not used for {component_type}"
            )
        if not rid:
            raise CommandExecutionError(
                f"Unable to resolve check-set resourceId for {component_type} in domain {domain_id}"
            )
        return rid

    def start_precheck(self, upgrade_id, domain_id, bundle_id, component_type):
        component_type = _component(component_type)
        if component_type == "SDDC_MANAGER":
            return {
                "skipped": True,
                "reason": "SDDC_MANAGER upgrade is created with draftMode=false and self-starts",
            }
        to_version = self._component_to_version(bundle_id, component_type)
        entry = {"resourceType": component_type, "resourceTargetVersion": to_version}
        rid = self._precheck_resource_id(domain_id, component_type)
        if rid is not None:
            entry["resourceId"] = rid
        q = self.client.post(
            "/v1/system/check-sets/queries",
            {
                "checkSetType": "UPGRADE",
                "domains": [{"domainId": domain_id, "resources": [entry]}],
            },
        )
        query_id = q.get("queryId")
        resources = q.get("resources") or []
        if not query_id or not resources:
            raise CommandExecutionError("Check-set query did not resolve target state")
        trigger_resources = []
        for resource in resources:
            checks = [
                {"checkSetId": c["checkSetId"]}
                for c in resource.get("checkSets", [])
                if c.get("checkSetId")
            ]
            if not resource.get("resourceId") or not checks:
                raise CommandExecutionError(
                    "Check-set query returned no selectable checks for a resource"
                )
            selected = {
                k: resource[k]
                for k in ("resourceName", "resourceId", "resourceType", "domain")
                if k in resource
            }
            selected["checkSets"] = checks
            trigger_resources.append(selected)
        metadata = {"targetVersion": to_version}
        payload = {"queryId": query_id, "resources": trigger_resources, "metadata": metadata}
        if component_type == "HOST":
            metadata["upgradeId"] = upgrade_id
        else:
            payload["contextVariables"] = {"upgradeId": upgrade_id}
        run = self.client.post("/v1/system/check-sets", payload)
        check_set_id = run.get("id")
        if not check_set_id:
            raise CommandExecutionError("Check-set trigger returned no id")
        return {
            "checkSetId": check_set_id,
            "queryId": query_id,
            "targetVersion": to_version,
            "response": run,
        }

    @staticmethod
    def _flatten_issues(node, out, resource_hint=None):
        if not isinstance(node, dict):
            return
        ctx = node.get("context") or {}
        if node.get("errorCode"):
            out.append(
                {
                    "severity": "ERROR",
                    "resource": resource_hint,
                    "validationName": ctx.get("validationName"),
                    "message": node.get("message"),
                }
            )
        notes = node.get("notifications")
        if notes:
            for n in notes:
                if n.get("severity") in {"ERROR", "WARNING"}:
                    out.append(
                        {
                            "severity": n.get("severity"),
                            "resource": resource_hint,
                            "validationName": ctx.get("validationName"),
                            "message": n.get("message"),
                        }
                    )
        else:
            resource_hint = ctx.get("entityName") or ctx.get("description") or resource_hint
        for child in node.get("nestedErrors") or []:
            VcfUpgradeProvider._flatten_issues(child, out, resource_hint)

    def precheck_status(self, check_set_id):
        data = self.client.get(f"/v1/system/check-sets/{_id(check_set_id, 'check_set_id')}")
        vr = data.get("validationResult")
        status = str(data.get("status", "UNKNOWN")).upper()
        summaries = (data.get("presentedArtifactsMap") or {}).get("validation-domain-summary") or []
        if not isinstance(summaries, list) or (vr is not None and not isinstance(vr, dict)):
            raise CommandExecutionError("Malformed check-set validation result")
        issues = []
        if vr is not None:
            self._flatten_issues(vr, issues)
        failed = status in FAIL_UPGRADE or bool((vr or {}).get("errorCode"))
        failed = failed or any(i.get("severity") == "ERROR" for i in issues)
        failed = failed or any(
            (x.get("criticalGapsCount") or 0) > 0 or (x.get("errorValidationsCount") or 0) > 0
            for x in summaries
        )
        # A running response may already contain partial results. A terminal success
        # without a validation artifact is not evidence that the checks passed.
        finished = failed or (
            vr is not None and status not in {"IN_PROGRESS", "PENDING", "RUNNING"}
        )
        if status in SUCCESS_UPGRADE and vr is None:
            failed = finished = True
        return {
            "checkSetId": check_set_id,
            "status": status,
            "isFinished": finished,
            "failed": failed,
            "issues": issues,
            "response": data,
        }

    def wait_precheck(self, check_set_id, timeout=7200, interval=60, fail_on_error=True):
        fail_on_error = boolean(fail_on_error)
        deadline, interval = poll_settings(timeout, interval)
        last = None
        while time.monotonic() < deadline:
            last = self.precheck_status(check_set_id)
            self.log.info(
                "VCF precheck %s status=%s finished=%s failed=%s issues=%s",
                check_set_id,
                last.get("status"),
                last.get("isFinished"),
                last.get("failed"),
                len(last.get("issues") or []),
            )
            if last.get("isFinished"):
                if last.get("failed") and fail_on_error:
                    raise CommandExecutionError(
                        f"VCF precheck {check_set_id} failed; inspect get_precheck_status for details"
                    )
                return last
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
        raise CommandExecutionError(f"Timed out waiting for VCF precheck {check_set_id}")

    def validate_post_upgrade(
        self, domain_id, component_type, target_version=None, bundle_id=None, cluster_id=None
    ):
        """Verify inventory versions against the bundle's component target, not its VCF release."""
        component_type = _component(component_type)
        domain = self.client.get(f"/v1/domains/{_id(domain_id, 'domain_id')}")
        expected = (
            self._component_to_version(bundle_id, component_type) if bundle_id else target_version
        )
        if not expected:
            raise CommandExecutionError("A component target version is required for postvalidation")
        if component_type == "SDDC_MANAGER":
            items = [
                x
                for x in self.client.elements("/v1/sddc-managers")
                if (x.get("domain") or {}).get("id") == domain_id
            ]
        elif component_type == "NSX_T_MANAGER":
            rid = _id((domain.get("nsxtCluster") or {}).get("id"), "NSX cluster id")
            items = [self.client.get(f"/v1/nsxt-clusters/{rid}")]
        elif component_type == "VCENTER":
            items = [
                self.client.get(f"/v1/vcenters/{_id(x.get('id'), 'vCenter id')}")
                for x in domain.get("vcenters", [])
            ]
        else:
            cluster = self.client.get(f"/v1/clusters/{_id(cluster_id, 'cluster_id')}")
            if (cluster.get("domain") or {}).get("id") != domain_id:
                raise CommandExecutionError("HOST cluster does not belong to the selected domain")
            items = [
                self.client.get(f"/v1/hosts/{_id(x.get('id'), 'host id')}")
                for x in cluster.get("hosts", [])
            ]
        versions = [
            x.get("esxiVersion") if component_type == "HOST" else x.get("version") for x in items
        ]
        healthy = bool(items) and all(v and _version_match(expected, v) for v in versions)
        healthy = healthy and str(domain.get("status", "")).upper() == "ACTIVE"
        if component_type == "NSX_T_MANAGER":
            healthy = healthy and all(x.get("status") == "STABLE" for x in items)
        if component_type == "HOST":
            healthy = healthy and cluster.get("status") == "ACTIVE"
            healthy = healthy and all(x.get("configurationStatus") == "ACTIVE" for x in items)
        return {
            "healthy": healthy,
            "domainId": domain_id,
            "componentType": component_type,
            "domainStatus": domain.get("status"),
            "componentVersions": versions,
            "expectedVersion": expected,
        }

    def wait_upgrade(self, upgrade_id, timeout=43200, interval=60, tolerate_unreachable=True):
        deadline, interval = poll_settings(timeout, interval)
        last = None
        transient = 0
        while time.monotonic() < deadline:
            try:
                last = self.upgrade_status(upgrade_id)
                st = str(last.get("status", "UNKNOWN")).upper()
                transient = 0
                self.log.info("VCF upgrade %s status=%s", upgrade_id, st)
                if st in SUCCESS_UPGRADE:
                    resource_statuses = [
                        str(r.get("status", "")).upper()
                        for r in last.get("resourceUpgradeSpecs", [])
                    ]
                    if any(
                        status and status not in SUCCESS_UPGRADE for status in resource_statuses
                    ):
                        raise CommandExecutionError("Upgrade resources have not all succeeded")
                    return {
                        "upgradeId": upgrade_id,
                        "upgradeStatus": st,
                        "changed": True,
                        "response": last,
                    }
                if st in FAIL_UPGRADE:
                    raise CommandExecutionError(f"VCF upgrade {upgrade_id} ended with {st}")
            except (SddcConnectionError, SddcHttpError) as exc:
                if isinstance(exc, SddcHttpError) and exc.status_code not in {
                    408,
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    raise
                if not boolean(tolerate_unreachable):
                    raise
                transient += 1
                self.log.warning("VCF status temporarily unreachable (attempt %s)", transient)
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
        raise CommandExecutionError(f"Timed out waiting for VCF upgrade {upgrade_id}")


def get_provider(opts, profile=None):
    """Use the same connection pillar/profile resolution as other SDDC clients."""
    from saltext.vcf.utils import sddc

    root = opts.get("pillar", {}).get("saltext.vcf") or opts.get("saltext.vcf") or {}
    if profile and "sddc_manager" not in root.get("profiles", {}).get(profile, {}):
        raise CommandExecutionError("Unknown SDDC Manager profile")
    cfg = sddc.get_config(opts, profile=profile)
    connection = root.get("sddc_manager", {})
    if profile:
        connection = root.get("profiles", {}).get(profile, {}).get("sddc_manager", connection)
    cfg.update(
        {key: connection[key] for key in ("protocol", "port", "timeout") if key in connection}
    )
    return VcfUpgradeProvider(**cfg)
