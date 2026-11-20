# pylint: disable=consider-using-f-string,raise-missing-from
"""VCF management components upgrade client.

The management components are upgraded through the Fleet Lifecycle upgrade-plan API, so this client
reuses the Fleet Lifecycle authentication (OpsToken from VCF Operations exchanged for a ``fleet-lcm``
JWT) and task polling from :class:`FleetLcmClient`. Mirrors ``upgrade_vcf_management_components.sh``:

* ``GET   /fleet-lcm/v1/upgrade-plans``                      - the active upgrade plan ``id``
* ``GET   /fleet-lcm/v1/release-versions/target-versions``   - releases with per-component ``versions``
* ``PATCH /fleet-lcm/v1/upgrade-plans/{id}``                 - set ``spec.desiredSoftware``
* ``GET   /fleet-lcm/v1/components``                         - component inventory
* ``GET   /fleet-lcm/v1/upgrade-plans/{id}``                 - per-component ``status`` / ``dependsOn``
* ``POST  /fleet-lcm/v1/upgrade-plans/{id}?action=precheck`` - precheck the ``componentsFilter``
* ``POST  /fleet-lcm/v1/upgrade-plans/{id}?action=apply``    - apply to the ``componentsFilter``

The action body is ``UpgradePlanActionRequest``: ``{"componentsFilter": [{"id": "<component id>"}]}``.
Without ``componentsFilter`` (or with an unknown key) the action covers the WHOLE plan, in parallel.

Components are upgraded one at a time in :data:`UPGRADE_ORDER`.
"""

import re
import time

from saltext.vcf.clients.fleet_lcm import RUNNING_STATES
from saltext.vcf.clients.fleet_lcm import FleetLcmClient
from saltext.vcf.clients.fleet_lcm import FleetLcmError

# Mandatory upgrade order as (componentType, label). The componentType values are the expected
# Fleet Lifecycle type names; override them with the ``order`` argument if the inventory differs.
UPGRADE_ORDER = (
    ("VCF_SDDC_LCM", "SDDC Lifecycle Mgmt (SDDC LCM)"),
    ("OPS", "VCF Operations"),
    ("VSP", "Management VCF Services Platform"),
    ("VCFA", "VCF Automation (VCF-A)"),
    ("OPS_NETWORKS", "VCF Networks"),
    ("SALT_RAAS", "Salt RaaS Mgmt"),
    ("SALT", "Salt Master Mgmt"),
    ("OPS_DATA_PLATFORM", "VODAP (Real-time metrics)"),
    ("OPS_LOGS", "LOGS"),
    ("TELEMETRY_ACCEPTOR", "Telemetry Mgmt"),
    ("VIDB", "Identity Broker Mgmt"),
    ("VCF_FLEET_DEPOT", "Fleet Depot Service (Software Depot Mgmt)"),
)


# Components upgraded as part of another component, so they are neither queued nor warned about.
IGNORED_TYPES = ("VCF_OPS_CLOUD_PROXY",)  # part of OPS


# Per-component status in an upgrade plan (UpgradePlanComponent.status).
SKIP_STATUSES = ("ON_TARGET", "HIGHER_THAN_TARGET")  # nothing to upgrade
BLOCKING_STATUSES = ("INELIGIBLE", "PENDING")  # not ready: do not submit anything for it


def _norm(value):
    """Type names match ignoring case and punctuation."""
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _elements(payload, keys=("elements",)):
    """List responses are a bare list or wrapped in one of ``keys`` (``/components`` uses ``components``)."""
    if isinstance(payload, dict):
        for key in keys:
            if payload.get(key):
                return payload[key]
        return []
    return payload or []


def release_version(release):
    if isinstance(release, dict):
        version = release.get("version") or release.get("targetVersion")
        return str(version) if version else None
    return str(release) if release else None


class MgmtComponentsUpgradeClient(FleetLcmClient):
    def list_plans(self):
        return [
            p
            for p in _elements(self.request("GET", "/fleet-lcm/v1/upgrade-plans"))
            if isinstance(p, dict)
        ]

    @staticmethod
    def select_plan(plans, plan_id=None):
        """Pick the plan to use; returns ``(plan, warnings)``.

        An explicit ``plan_id`` wins. Otherwise prefer ``READY`` plans, then the most recently updated,
        and warn when more than one candidate exists because the choice is then a judgement call.
        """
        if plan_id:
            for plan in plans:
                if plan.get("id") == plan_id:
                    return plan, []
            raise FleetLcmError(
                "Upgrade plan {} not found. Available: {}".format(
                    plan_id, ", ".join(str(p.get("id")) for p in plans) or "none"
                )
            )
        candidates = [p for p in plans if p.get("id")]
        if not candidates:
            raise FleetLcmError("No active upgrade plan found.")
        ready = [p for p in candidates if p.get("status") == "READY"] or candidates
        plan = sorted(ready, key=lambda p: p.get("updateTime") or "")[-1]
        warnings = []
        if len(candidates) > 1:
            warnings.append(
                "{} upgrade plans exist ({}); using {}. Pass plan_id to choose another.".format(
                    len(candidates), ", ".join(str(p["id"]) for p in candidates), plan["id"]
                )
            )
        return plan, warnings

    def get_upgrade_plan_id(self, plan_id=None):
        return self.select_plan(self.list_plans(), plan_id)[0]["id"]

    def list_releases(self):
        return [
            r
            for r in _elements(
                self.request("GET", "/fleet-lcm/v1/release-versions/target-versions")
            )
            if release_version(r)
        ]

    @staticmethod
    def select_release(releases, requested=None):
        """Return the requested release, or the first available one."""
        if requested:
            for release in releases:
                if release_version(release) == str(requested):
                    return release
            raise FleetLcmError(
                "Target version {} is not available. Available: {}".format(
                    requested, ", ".join(release_version(r) for r in releases) or "none"
                )
            )
        if not releases:
            raise FleetLcmError(
                "No target upgrade versions found. Ensure your software depot metadata is synced."
            )
        return releases[0]

    @staticmethod
    def desired_state(release):
        """Every component of the release at its newest listed version.

        Only release components are sent: the plan may hold others (for example optional services)
        that ``VCF_FLEET_ADMIN`` is not allowed to target, and sending them gets the PATCH a 403.
        """
        components = []
        for comp in release.get("components") or []:
            if isinstance(comp, dict) and comp.get("versions"):
                entry = {"type": comp.get("type"), "version": comp["versions"][0]}
                if comp.get("publicName"):
                    entry["publicName"] = comp["publicName"]
                components.append(entry)
        if not components:
            raise FleetLcmError(f"Release {release_version(release)} lists no component versions.")
        return {
            "spec": {
                "desiredSoftware": {"version": release_version(release), "components": components}
            }
        }

    @staticmethod
    def plan_matches(plan, desired_state):
        """True when the plan already targets this release version and every one of its components."""
        want = desired_state["spec"]["desiredSoftware"]
        have = ((plan or {}).get("spec") or {}).get("desiredSoftware") or {}
        if str(have.get("version")) != str(want["version"]):
            return False
        current = {_norm(c.get("type")): c.get("version") for c in have.get("components") or []}
        return all(current.get(_norm(c["type"])) == c["version"] for c in want["components"])

    @staticmethod
    def _task_id(response, what, required=True):
        task_id = response.get("id") if isinstance(response, dict) else None
        if required and not task_id:
            raise FleetLcmError(f"Fleet Lifecycle returned no task id for {what}: {response}")
        return task_id

    def set_desired_state(self, plan_id, desired_state):
        """PATCH the plan. Returns a task id only if the response is a task.

        The PATCH normally answers with the updated upgrade plan, whose ``id`` is the plan id, not a
        task id; polling that as a task gets HTTP 404 forever. Use :meth:`wait_for_plan_ready` to wait
        for the plan to finish syncing.
        """
        response = self.request("PATCH", f"/fleet-lcm/v1/upgrade-plans/{plan_id}", desired_state)
        if isinstance(response, dict) and ("spec" in response or "executions" in response):
            return None
        return self._task_id(response, "PATCH upgrade plan", required=False)

    def wait_for_plan_ready(
        self,
        plan_id,
        desired_state,
        timeout_seconds=3600,
        poll_interval_seconds=15,
        sleep=time.sleep,
    ):
        """Poll the plan until it is ``READY`` and targets ``desired_state`` (it syncs after a PATCH)."""
        deadline = time.monotonic() + timeout_seconds
        status = None
        while True:
            try:
                plan = self.request("GET", f"/fleet-lcm/v1/upgrade-plans/{plan_id}") or {}
                status = plan.get("status")
                if status in ("READY", "COMPLETED") and self.plan_matches(plan, desired_state):
                    return {"plan_id": plan_id, "status": status}
            except FleetLcmError as exc:
                self.log.info("Fleet Lifecycle not reachable yet, retrying: %s", exc)
            if time.monotonic() >= deadline:
                raise FleetLcmError(
                    f"Upgrade plan {plan_id} did not become READY with the desired software within "
                    f"{timeout_seconds}s (last status {status})"
                )
            sleep(poll_interval_seconds)

    def list_components(self):
        return [
            c
            for c in _elements(
                self.request("GET", "/fleet-lcm/v1/components"), ("components", "elements")
            )
            if isinstance(c, dict)
        ]

    @staticmethod
    def build_queue(components, release, order=None):
        """Resolve the ordered upgrade queue from the inventory and the target release.

        Returns ``(queue, warnings)``. Each queue item has ``id``, ``type``, ``label``, ``fqdn``,
        ``current`` and ``desired``. Order entries without an inventory component, or without a
        version in the release, are skipped with a warning; so are deployed release components
        that are missing from the order (they are NOT upgraded). Nothing matching is an error.
        """
        order = order or UPGRADE_ORDER
        desired = {
            _norm(c.get("type")): c["versions"][0]
            for c in release.get("components") or []
            if isinstance(c, dict) and c.get("versions")
        }
        queue, warnings = [], []
        for ctype, label in order:
            matches = [
                c
                for c in components
                if _norm(c.get("componentType")) == _norm(ctype) and c.get("id")
            ]
            if not matches:
                warnings.append(f"No {label} component (type {ctype}) in the inventory; skipping.")
            elif not desired.get(_norm(ctype)):
                warnings.append(
                    f"The release lists no version for {label} (type {ctype}); skipping."
                )
            else:
                queue.extend(
                    {
                        "id": comp["id"],
                        "type": ctype,
                        "label": label,
                        "fqdn": comp.get("fqdn"),
                        "current": comp.get("currentVersion") or comp.get("version"),
                        "desired": desired[_norm(ctype)],
                    }
                    for comp in matches
                )
        ordered = {_norm(t) for t, _ in order} | {_norm(t) for t in IGNORED_TYPES}
        for comp in components:
            ctype = _norm(comp.get("componentType"))
            if ctype in desired and ctype not in ordered:
                warnings.append(
                    "{} is deployed and in the release but not in the upgrade order; it will NOT be upgraded.".format(
                        comp.get("componentType")
                    )
                )
        if not queue:
            raise FleetLcmError(
                "No inventory component matched the upgrade order. Inventory types: {}. "
                "Run vcf_mgmt_components_upgrade.inspect_api to see the raw responses.".format(
                    ", ".join(sorted({str(c.get("componentType")) for c in components})) or "none"
                )
            )
        return queue, warnings

    def get_plan_components(self, plan_id, component_id=None):
        """Plan components keyed by id, with ``status``, ``dependsOn`` and ``messages``."""
        path = f"/fleet-lcm/v1/upgrade-plans/{plan_id}?includeAllComponents=true&componentsPageSize=200"
        if component_id:
            path += f"&componentId={component_id}"
        plan = self.request("GET", path)
        page = plan.get("components") if isinstance(plan, dict) else None
        return {c["id"]: c for c in _elements(page or {}) if isinstance(c, dict) and c.get("id")}

    @staticmethod
    def component_problem(plan_component):
        """Readable reason a plan component is not ready: its status, messages and dependencies."""
        texts = []
        for msg in plan_component.get("messages") or []:
            inner = msg.get("message") or {}
            text = inner.get("localizedMessage") or inner.get("defaultMessage")
            if text:
                texts.append(f"{msg.get('level', 'INFO')}: {text}")
        reason = f"status {plan_component.get('status')}"
        if texts:
            reason += "; " + "; ".join(texts)
        if plan_component.get("dependsOn"):
            reason += "; depends on " + ", ".join(plan_component["dependsOn"])
        return reason

    def list_tasks(self):
        return [
            t for t in _elements(self.request("GET", "/fleet-lcm/v1/tasks")) if isinstance(t, dict)
        ]

    def running_workflows(self):
        """Precheck/apply tasks that are still running; starting another on top of them is unsafe."""
        return [
            t
            for t in self.list_tasks()
            if t.get("status") in RUNNING_STATES and t.get("type") in ("APPLY", "PRECHECK")
        ]

    def assert_scope(
        self, parent_task_id, component_id, wait_seconds=15, attempts=3, sleep=time.sleep
    ):
        """Fail unless the workflow behind ``parent_task_id`` targets only ``component_id``.

        Fleet Lifecycle fans a plan action out into child tasks (``parentTaskId``, ``resourceId``).
        If the appliance ignored the component scoping, the children cover other components and
        continuing would upgrade them all at once, out of order.
        """
        children = []
        for _ in range(attempts):
            sleep(wait_seconds)  # children are created over a few seconds
            children = [t for t in self.list_tasks() if t.get("parentTaskId") == parent_task_id]
            if children:
                break
        if not children:
            raise FleetLcmError(
                f"Cannot verify the scope of task {parent_task_id}: no child tasks found. Not continuing."
            )
        others = sorted(
            {
                str(t.get("resourceType") or t.get("resourceId"))
                for t in children
                if t.get("resourceId") != component_id
            }
        )
        if others:
            raise FleetLcmError(
                "Fleet Lifecycle ran task {} for more than the requested component (also: {}). "
                "Per-component scoping is not honored, so the upgrade order cannot be enforced; "
                "aborting before any apply.".format(parent_task_id, ", ".join(others))
            )

    def _plan_action(self, action, plan_id, component_id):
        response = self.request(
            "POST",
            f"/fleet-lcm/v1/upgrade-plans/{plan_id}?action={action}",
            {"componentsFilter": [{"id": component_id}]},
        )
        return self._task_id(response, f"upgrade plan {action}")

    def precheck(self, plan_id, component_id):
        return self._plan_action("precheck", plan_id, component_id)

    def apply(self, plan_id, component_id):
        return self._plan_action("apply", plan_id, component_id)
