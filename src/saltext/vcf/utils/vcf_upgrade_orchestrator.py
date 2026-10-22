"""Serial, checkpointed VCF upgrade orchestration.

An intent is persisted before each non-idempotent submission. If the process
loses the submission result, recovery stops for reconciliation rather than
risking a duplicate upgrade. Only a confirmed remote ID permits automatic resume.
"""

import fcntl
import hashlib
import inspect
import json
import logging
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from pathlib import Path

from saltext.vcf.clients.vcf_upgrade import VcfUpgradeProvider
from saltext.vcf.clients.vcf_upgrade import _component
from saltext.vcf.clients.vcf_upgrade import _version
from saltext.vcf.utils.vcf_upgrade_transport import CommandExecutionError
from saltext.vcf.utils.vcf_upgrade_transport import boolean
from saltext.vcf.utils.vcf_upgrade_transport import poll_settings


class VcfUpgradeOrchestrator:
    def __init__(
        self, provider, logger=None, checkpoint_file="/var/cache/salt/minion/vcf-upgrade.json"
    ):
        self.provider = provider
        self.log = logger or logging.getLogger(__name__)
        self.checkpoint_file = str(checkpoint_file)

    @staticmethod
    def result(_changed, comment, **data):
        data.pop("changed", None)
        return {"changed": bool(_changed), "comment": comment, "data": data}

    def _load(self):
        try:
            with open(self.checkpoint_file, encoding="utf-8") as stream:
                state = json.load(stream)
        except FileNotFoundError:
            return {"components": {}}
        except (ValueError, OSError) as exc:
            raise CommandExecutionError(
                "Cannot read checkpoint; reconcile it before retrying"
            ) from exc
        if not isinstance(state, dict) or not isinstance(state.get("components"), dict):
            raise CommandExecutionError("Invalid checkpoint; reconcile it before retrying")
        return state

    @contextmanager
    def _lock(self):
        path = Path(self.checkpoint_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path) + ".lock", os.O_CREAT | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise CommandExecutionError("Another upgrade uses this checkpoint") from None
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def _save(self, state):
        directory = str(Path(self.checkpoint_file).parent)
        fd, temporary = tempfile.mkstemp(prefix=".vcf-upgrade-", dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(state, stream, indent=2, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.checkpoint_file)
            directory_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _mark(self, state, key, phase, **data):
        checkpoint = state.setdefault("components", {}).setdefault(key, {})
        checkpoint.update(data)
        checkpoint["phase"] = phase
        checkpoint["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self._save(state)

    def bundle_downloaded(
        self, component_type, target_version, wait=True, timeout=14400, interval=60, dry_run=False
    ):
        component_type = _component(component_type)
        if not target_version:
            raise CommandExecutionError("An explicit target version/build is required")
        poll_settings(timeout, interval)
        dry_run, wait = boolean(dry_run), boolean(wait)
        existing = self.provider.find_bundle(component_type, target_version, "SUCCESSFUL")
        if existing:
            return self.result(
                False,
                "VCF upgrade bundle already downloaded",
                bundleId=existing["id"],
                version=existing.get("version"),
                downloadStatus="SUCCESSFUL",
            )
        if dry_run:
            bundle = self.provider.find_bundle(component_type, target_version)
            if not bundle:
                raise CommandExecutionError("No matching bundle found")
            return self.result(
                True, "VCF upgrade bundle would be downloaded", bundleId=bundle["id"]
            )
        data = self.provider.ensure_bundle_download(component_type, target_version)
        changed = data.get("changed", False)
        if wait and data.get("downloadStatus") != "SUCCESSFUL":
            data.update(self.provider.wait_bundle(data["bundleId"], timeout, interval))
        return self.result(
            changed, "VCF upgrade bundle ready" if wait else "Bundle download submitted", **data
        )

    def upgrade_created(self, **kwargs):
        dry = boolean(kwargs.pop("dry_run", False))
        # Raw creation is imperative; checkpointed states call sequence/full_upgrade.
        if dry:
            return self.result(True, "VCF upgrade would be created", **kwargs)
        return self.result(True, "VCF upgrade created", **self.provider.create_upgrade(**kwargs))

    def upgrade_executed(
        self, upgrade_id, schedule_for_later=False, scheduled_timestamp=None, dry_run=False
    ):
        status = str(self.provider.upgrade_status(upgrade_id).get("status", "")).upper()
        if status in {
            "SCHEDULED",
            "IN_PROGRESS",
            "COMPLETED_WITH_SUCCESS",
            "SUCCESSFUL",
            "SUCCESS",
        }:
            return self.result(False, f"VCF upgrade already {status}", upgradeId=upgrade_id)
        if status != "DRAFT":
            raise CommandExecutionError(f"Upgrade cannot execute from {status or 'UNKNOWN'}")
        if boolean(dry_run):
            return self.result(True, "VCF upgrade would be executed", upgradeId=upgrade_id)
        data = self.provider.execute_upgrade(upgrade_id, schedule_for_later, scheduled_timestamp)
        return self.result(
            data.get("changed", True), "VCF upgrade execution submitted", upgradeId=upgrade_id
        )

    def upgrade_monitored(self, upgrade_id, timeout=43200, interval=60):
        return self.result(
            False,
            "VCF upgrade completed",
            **self.provider.wait_upgrade(upgrade_id, timeout, interval),
        )

    def _health(self, plan, ctype, options):
        health = self.provider.validate_post_upgrade(
            plan["domainId"],
            ctype,
            plan["targetVersion"],
            bundle_id=plan["bundleId"],
            cluster_id=options.get("cluster_id"),
        )
        if not health.get("healthy"):
            raise CommandExecutionError(f"Post-upgrade inventory validation failed for {ctype}")
        return health

    def _component(self, spec, target, domain_id, lifecycle, state, create_only=False):
        ctype, key = spec["type"], spec["name"]
        cp = state.get("components", {}).get(key, {})
        options = spec.get("options") or {}
        phase = cp.get("phase")
        if phase == "CREATING" or phase == "PRECHECK_SUBMITTING":
            raise CommandExecutionError(
                f"{key}: submission outcome is unknown; reconcile remote IDs in checkpoint before retrying"
            )
        if cp.get("upgradeId"):
            plan = {k: cp[k] for k in ("domainId", "bundleId", "targetVersion")}
            uid = cp["upgradeId"]
            if phase == "COMPLETED":
                self._health(plan, ctype, options)
                return {"component": key, "skipped": True, "upgradeId": uid, "changed": False}
            changed = False
        else:
            bundle = self.bundle_downloaded(
                ctype,
                target,
                True,
                lifecycle["bundle_timeout_seconds"],
                lifecycle["poll_interval_seconds"],
            )
            changed = bundle["changed"]
            plan = self.provider.plan(ctype, target, spec.get("domain_id") or domain_id)
            self._mark(state, key, "CREATING", **plan)
            created = self.provider.create_upgrade(
                domain_id=plan["domainId"],
                bundle_id=plan["bundleId"],
                target_version=plan["targetVersion"],
                component_type=ctype,
                draft_mode=spec.get("draft_mode"),
                schedule_for_later=spec.get("schedule_for_later", False),
                scheduled_timestamp=spec.get("scheduled_timestamp"),
                **options,
            )
            uid = created["upgradeId"]
            changed = True
            self._mark(state, key, "CREATED", upgradeId=uid, draftModeUsed=created["draftModeUsed"])
            cp = state["components"][key]
        phase = cp["phase"]
        if create_only:
            return {
                "component": key,
                "upgradeId": uid,
                "changed": changed,
                "draftModeUsed": cp.get("draftModeUsed"),
                "targetVersion": plan["targetVersion"],
            }
        if cp.get("draftModeUsed") and phase not in {
            "EXECUTING",
            "EXECUTE_SUBMITTING",
            "UPGRADE_COMPLETED",
        }:
            # Creation returns before a DRAFT is necessarily visible.
            self.provider.wait_draft(
                uid, lifecycle["precheck_timeout_seconds"], lifecycle["poll_interval_seconds"]
            )
            if not cp.get("checkSetId"):
                self._mark(state, key, "PRECHECK_SUBMITTING")
                precheck = self.provider.start_precheck(
                    uid, plan["domainId"], plan["bundleId"], ctype
                )
                self._mark(state, key, "PRECHECK_RUNNING", checkSetId=precheck["checkSetId"])
                changed = True
            result = self.provider.wait_precheck(
                cp["checkSetId"],
                lifecycle["precheck_timeout_seconds"],
                lifecycle["poll_interval_seconds"],
                True,
            )
            if result.get("failed"):
                raise CommandExecutionError(f"Precheck failed for {key}")
            self._mark(state, key, "PRECHECK_COMPLETED")
            self._mark(state, key, "EXECUTE_SUBMITTING")
            executed = self.provider.execute_upgrade(
                uid, spec.get("schedule_for_later", False), spec.get("scheduled_timestamp")
            )
            changed = changed or executed.get("changed", False)
            self._mark(state, key, "EXECUTING")
        elif phase == "EXECUTE_SUBMITTING":
            # A lost PATCH reply must not result in another commit request.
            status = str(self.provider.upgrade_status(uid).get("status", "")).upper()
            if status in {"DRAFT", "PENDING"}:
                raise CommandExecutionError(f"{key}: reconcile uncertain execution before retrying")
        monitored = self.provider.wait_upgrade(
            uid, lifecycle["upgrade_timeout_seconds"], lifecycle["poll_interval_seconds"]
        )
        self._mark(state, key, "UPGRADE_COMPLETED", upgradeStatus=monitored["upgradeStatus"])
        health = self._health(plan, ctype, options)
        self._mark(state, key, "COMPLETED", health=health)
        return {
            "component": key,
            "upgradeId": uid,
            "targetVersion": plan["targetVersion"],
            "status": "COMPLETED",
            "health": health,
            "changed": changed,
        }

    def _expand(self, components, target_version, domain_id):
        if not isinstance(components, (list, tuple)) or not components:
            raise CommandExecutionError("An explicit nonempty sequence is required")
        expanded = []
        for raw in components:
            spec = {"type": raw} if isinstance(raw, str) else dict(raw)
            if not boolean(spec.get("enabled", True), "enabled"):
                continue
            spec["type"] = _component(spec.get("type"))
            if (
                spec.get("force")
                or spec.get("allow_upgrade_on_precheck_failure")
                or spec.get("fail_on_precheck_error", True) is not True
            ):
                raise CommandExecutionError("Force and precheck bypasses are not supported")
            clusters = spec.pop("clusters", None)
            if clusters is not None:
                if spec["type"] != "HOST" or not clusters:
                    raise CommandExecutionError("clusters must be a nonempty HOST cluster list")
                for cluster in clusters:
                    item = dict(spec)
                    item["name"] = "HOST:" + str(cluster.get("cluster_id", ""))
                    item["options"] = dict(spec.get("options") or {})
                    item["options"].update({k: v for k, v in cluster.items() if k != "name"})
                    expanded.append(item)
            else:
                spec.setdefault("name", spec["type"])
                expanded.append(spec)
        keys = set()
        for spec in expanded:
            if spec["name"] in keys:
                raise CommandExecutionError("Sequence component names must be unique")
            keys.add(spec["name"])
            target = spec.get("target_build") or spec.get("target_version") or target_version
            if not target:
                raise CommandExecutionError(f"No target configured for {spec['name']}")
            _version(target)
            spec["target_version"] = target
            spec["domain_id"] = spec.get("domain_id") or domain_id
            draft = spec.get("draft_mode")
            if draft is not None and boolean(draft) != (spec["type"] != "SDDC_MANAGER"):
                raise CommandExecutionError(
                    "SDDC_MANAGER requires direct mode; other components require drafts"
                )
            if boolean(spec.get("schedule_for_later", False)) and not spec.get(
                "scheduled_timestamp"
            ):
                raise CommandExecutionError("scheduled_timestamp is required")
            options = spec.get("options") or {}
            reserved = {
                "domain_id",
                "bundle_id",
                "target_version",
                "component_type",
                "draft_mode",
                "schedule_for_later",
                "scheduled_timestamp",
                "self",
            }
            valid = (
                set(inspect.signature(VcfUpgradeProvider.build_upgrade_payload).parameters)
                - reserved
            )
            if set(options) - valid:
                raise CommandExecutionError(
                    f"Unsupported upgrade options: {sorted(set(options) - valid)}"
                )
            if spec["type"] == "HOST" and not all(
                options.get(k) for k in ("cluster_id", "personality_id")
            ):
                raise CommandExecutionError("HOST requires cluster_id and personality_id")
        return expanded

    def sequence(
        self,
        components,
        target_version=None,
        domain_id=None,
        lifecycle=None,
        dry_run=False,
        reset_checkpoint=False,
        create_only=False,
    ):
        dry_run, reset_checkpoint = boolean(dry_run), boolean(reset_checkpoint)
        life = {
            "bundle_timeout_seconds": 14400,
            "precheck_timeout_seconds": 7200,
            "upgrade_timeout_seconds": 43200,
            "poll_interval_seconds": 60,
        }
        life.update(lifecycle or {})
        for key in (
            "bundle_timeout_seconds",
            "precheck_timeout_seconds",
            "upgrade_timeout_seconds",
        ):
            poll_settings(life[key], life["poll_interval_seconds"])
        # Validate the complete sequence before submitting any component.
        expanded = self._expand(components, target_version, domain_id)
        if not expanded:
            return self.result(False, "All sequence components are disabled", sequence=[])
        for spec in expanded:
            spec["domain_id"] = spec["domain_id"] or self.provider.management_domain_id()
            bundle = self.provider.find_bundle(spec["type"], spec["target_version"])
            if not bundle:
                raise CommandExecutionError(f"No bundle found for {spec['name']}")
            self.provider.build_upgrade_payload(
                spec["domain_id"],
                bundle["id"],
                bundle["version"],
                spec["type"],
                draft_mode=spec.get("draft_mode"),
                schedule_for_later=spec.get("schedule_for_later", False),
                scheduled_timestamp=spec.get("scheduled_timestamp"),
                **(spec.get("options") or {}),
            )
        identity = {"endpoint": self.provider.client.base_url, "sequence": expanded}
        fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        if dry_run:
            state = self._load()
            if state.get("components") and state.get("fingerprint") != fingerprint:
                raise CommandExecutionError(
                    "Checkpoint belongs to a different endpoint, target or sequence"
                )
            results = []
            for spec in expanded:
                checkpoint = state.get("components", {}).get(spec["name"], {})
                if checkpoint.get("phase") == "COMPLETED":
                    self._health(checkpoint, spec["type"], spec.get("options") or {})
                    results.append({"component": spec["name"], "skipped": True})
                else:
                    bundle = self.bundle_downloaded(
                        spec["type"], spec["target_version"], dry_run=True
                    )
                    results.append({"component": spec["name"], "dryRun": True, "bundle": bundle})
            changed = any(not result.get("skipped") for result in results)
            return self.result(
                changed,
                "VCF upgrade sequence would run" if changed else "VCF upgrade already completed",
                sequence=results,
            )
        with self._lock():
            state = self._load()
            if state.get("components"):
                if reset_checkpoint:
                    raise CommandExecutionError(
                        "Cannot reset a populated checkpoint; archive it after remote reconciliation"
                    )
                if state.get("fingerprint") != fingerprint:
                    raise CommandExecutionError(
                        "Checkpoint belongs to a different endpoint, target or sequence"
                    )
            state["fingerprint"] = fingerprint
            self._save(state)
            results = [
                self._component(
                    spec, spec["target_version"], spec["domain_id"], life, state, create_only
                )
                for spec in expanded
            ]
        return self.result(
            any(r.get("changed") for r in results),
            "VCF upgrade creation ensured" if create_only else "VCF upgrade sequence completed",
            sequence=results,
            checkpointFile=self.checkpoint_file,
        )

    def full_upgrade(
        self,
        component_type,
        target_version,
        domain_id=None,
        bundle_timeout=14400,
        upgrade_timeout=43200,
        interval=60,
        schedule_for_later=False,
        scheduled_timestamp=None,
        draft_mode=None,
        dry_run=False,
        **options,
    ):
        """Use the same resumable workflow for a single component."""
        spec = {
            "type": component_type,
            "draft_mode": draft_mode,
            "schedule_for_later": schedule_for_later,
            "scheduled_timestamp": scheduled_timestamp,
            "options": options,
        }
        return self.sequence(
            [spec],
            target_version,
            domain_id,
            {
                "bundle_timeout_seconds": bundle_timeout,
                "upgrade_timeout_seconds": upgrade_timeout,
                "poll_interval_seconds": interval,
            },
            dry_run,
        )
