"""Tests for modules.vcf_mgmt_components_upgrade."""

import pytest

from saltext.vcf.clients.mgmt_components_upgrade import MgmtComponentsUpgradeClient
from saltext.vcf.modules import vcf_mgmt_components_upgrade as mod

RELEASE = {
    "version": "9.1.0",
    "components": [
        {"type": "VCF_FLEET_DEPOT", "versions": ["9.1.0"]},
        {"type": "VSP", "versions": ["2.0"]},
        {"type": "VCF_SDDC_LCM", "versions": ["9.1.0"]},
    ],
}
INVENTORY = [  # deliberately not in upgrade order
    {"id": "d", "componentType": "VCF_FLEET_DEPOT", "fqdn": "depot", "currentVersion": "9.0.0"},
    {"id": "v", "componentType": "VSP", "fqdn": "vsp", "currentVersion": "1.0"},
    {"id": "s", "componentType": "VCF_SDDC_LCM", "fqdn": "sddc", "currentVersion": "9.0.0"},
]


class FakeClient:
    select_release = staticmethod(MgmtComponentsUpgradeClient.select_release)
    desired_state = staticmethod(MgmtComponentsUpgradeClient.desired_state)
    select_plan = staticmethod(MgmtComponentsUpgradeClient.select_plan)
    plan_matches = staticmethod(MgmtComponentsUpgradeClient.plan_matches)
    component_problem = staticmethod(MgmtComponentsUpgradeClient.component_problem)
    build_queue = staticmethod(MgmtComponentsUpgradeClient.build_queue)

    def __init__(self):
        self.calls = []
        self.fail_on = None
        self.inventory = [dict(c) for c in INVENTORY]

    def list_components(self):
        return self.inventory

    def list_releases(self):
        return [RELEASE]

    def list_plans(self):
        return [{"id": "p1", "status": "READY"}]

    def get_upgrade_plan_id(self, plan_id=None):
        return plan_id or "p1"

    def wait_for_plan_ready(self, plan_id, desired, *_a):
        self.calls.append(("plan-ready", plan_id))
        return {"plan_id": plan_id, "status": "READY"}

    def set_desired_state(self, plan_id, desired):
        self.calls.append(("plan", plan_id, desired["spec"]["desiredSoftware"]["version"]))

    busy = ()
    scope_error = None
    plan_status = {}  # component id -> UpgradePlanComponent dict; missing means "not in plan"

    def get_plan_components(self, plan_id, component_id=None):
        return {k: {"id": k, **v} for k, v in self.plan_status.items() if component_id in (None, k)}

    def running_workflows(self):
        return list(self.busy)

    def assert_scope(self, task_id, component_id):
        if self.scope_error:
            raise self.scope_error

    def precheck(self, plan_id, component_id):
        self.calls.append(("precheck", component_id))
        return f"pre-{component_id}"

    def apply(self, plan_id, component_id):
        self.calls.append(("apply", component_id))
        return f"apply-{component_id}"

    def wait_for_task(self, task_id, *_a):
        if task_id == self.fail_on:
            raise RuntimeError(f"{task_id} failed")
        return {"task_id": task_id, "status": "SUCCEEDED"}


@pytest.fixture
def fake(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(mod, "_client", lambda **_k: client)
    monkeypatch.setattr(mod, "__salt__", {"pillar.get": lambda *a, **k: {}}, raising=False)
    return client


def test_virtual():
    assert mod.__virtual__() == "vcf_mgmt_components_upgrade"


def test_missing_host_fails(monkeypatch):
    monkeypatch.setattr(mod, "__salt__", {"pillar.get": lambda *a, **k: {}}, raising=False)
    with pytest.raises(Exception, match="host"):
        mod._client()
    with pytest.raises(Exception, match="ops_host"):
        mod._client(host="flt.example")


def test_validate_ready_reports_order(fake):
    res = mod.validate_ready()
    assert res["changed"] is False
    assert (
        "SDDC Lifecycle Mgmt (SDDC LCM) -> Management VCF Services Platform -> Fleet Depot"
        in res["comment"]
    )
    assert [c["id"] for c in res["data"]["queue"]] == ["s", "v", "d"]


def test_full_upgrade_is_sequential_in_mandatory_order(fake):
    res = mod.full_upgrade()
    assert fake.calls == [
        ("plan", "p1", "9.1.0"),
        ("plan-ready", "p1"),
        ("precheck", "s"),
        ("apply", "s"),
        ("precheck", "v"),
        ("apply", "v"),
        ("precheck", "d"),
        ("apply", "d"),
    ]
    assert (
        res["changed"]
        and [r["apply"] for r in res["data"]["apply"]["results"]] == ["SUCCEEDED"] * 3
    )


def test_refuses_to_start_while_upgrade_tasks_are_running(fake):
    fake.busy = [{"resourceType": "OPS", "type": "APPLY"}]
    with pytest.raises(Exception, match="already running.*OPS APPLY"):
        mod.apply_upgrade()
    assert fake.calls == []


def test_plan_wide_precheck_aborts_before_any_apply(fake):
    fake.scope_error = RuntimeError("scoping not honored")
    with pytest.raises(RuntimeError, match="scoping not honored"):
        mod.apply_upgrade()
    assert fake.calls == [("precheck", "s")]  # never reaches an apply


def test_on_target_status_in_plan_skips_component(fake):
    fake.plan_status = {
        "v": {"status": "ON_TARGET"},
        "s": {"status": "ELIGIBLE"},
        "d": {"status": "ELIGIBLE"},
    }
    res = mod.apply_upgrade()
    assert [c for c in fake.calls if c[0] == "apply"] == [("apply", "s"), ("apply", "d")]
    assert res["data"]["pending"] == [
        "SDDC Lifecycle Mgmt (SDDC LCM)",
        "Fleet Depot Service (Software Depot Mgmt)",
    ]


@pytest.mark.parametrize("status", ["INELIGIBLE", "PENDING"])
def test_not_ready_component_stops_the_run_untouched(fake, status):
    fake.plan_status = {
        "s": {"status": "ELIGIBLE"},
        "v": {
            "status": status,
            "dependsOn": ["OPS"],
            "messages": [{"level": "ERROR", "message": {"defaultMessage": "blocked"}}],
        },
        "d": {"status": "ELIGIBLE"},
    }
    with pytest.raises(Exception, match=f"not ready.*status {status}.*blocked.*depends on OPS"):
        mod.apply_upgrade()
    # SDDC LCM went first; VSP and everything after it was never touched.
    assert fake.calls == [("precheck", "s"), ("apply", "s")]


def test_status_changing_during_the_run_is_honoured(fake, monkeypatch):
    """A component that becomes ON_TARGET after an earlier upgrade is skipped via the live re-check."""
    fake.plan_status = {k: {"status": "ELIGIBLE"} for k in "svd"}
    original = fake.apply

    def apply_and_flip(plan_id, component_id):
        if component_id == "s":
            fake.plan_status["v"] = {"status": "ON_TARGET"}
        return original(plan_id, component_id)

    monkeypatch.setattr(fake, "apply", apply_and_flip)
    mod.apply_upgrade()
    assert [c for c in fake.calls if c[0] == "apply"] == [("apply", "s"), ("apply", "d")]


def test_component_missing_from_plan_is_warned_not_blocked(fake):
    res = mod.validate_ready()
    assert any("not in upgrade plan" in w for w in res["data"]["warnings"])
    mod.apply_upgrade()
    assert ("apply", "d") in fake.calls


def test_failure_stops_later_components(fake):
    fake.fail_on = "apply-v"
    with pytest.raises(RuntimeError, match="apply-v failed"):
        mod.apply_upgrade()
    assert ("precheck", "d") not in fake.calls and ("apply", "s") in fake.calls


def test_precheck_failure_never_applies_that_component(fake):
    fake.fail_on = "pre-s"
    with pytest.raises(RuntimeError):
        mod.apply_upgrade()
    assert fake.calls == [("precheck", "s")]


def test_components_at_target_are_skipped(fake):
    fake.inventory[1]["currentVersion"] = "2.0"
    mod.apply_upgrade()
    assert [c for c in fake.calls if c[0] == "apply"] == [("apply", "s"), ("apply", "d")]
    for comp, version in zip(fake.inventory, ["9.1.0", "2.0", "9.1.0"]):
        comp["currentVersion"] = version
    assert mod.apply_upgrade()["changed"] is False


def test_order_override_accepts_string(fake):
    mod.apply_upgrade(order="VCF_FLEET_DEPOT,VCF_SDDC_LCM")
    assert [c for c in fake.calls if c[0] == "apply"] == [("apply", "d"), ("apply", "s")]


def test_dry_run_submits_nothing(fake):
    res = mod.full_upgrade(dry_run=True)
    assert res["changed"] is True and fake.calls == []


def test_unknown_target_version_fails(fake):
    with pytest.raises(Exception, match="not available"):
        mod.validate_ready(target_version="1.0")


def test_configure_plan_waits_for_the_plan_not_a_task(fake):
    """Regression: the PATCH returns the plan; waiting must poll the plan, never GET /tasks/<plan id>."""
    res = mod.configure_plan()
    assert fake.calls == [("plan", "p1", "9.1.0"), ("plan-ready", "p1")]
    assert res["data"]["plan"]["status"] == "READY" and "task" not in res["data"]


def test_plan_already_at_target_is_not_patched(fake, monkeypatch):
    desired = MgmtComponentsUpgradeClient.desired_state(RELEASE)["spec"]["desiredSoftware"]
    plan = {"id": "p1", "spec": {"desiredSoftware": desired}}
    monkeypatch.setattr(fake, "list_plans", lambda: [plan])
    res = mod.configure_plan()
    assert res["changed"] is False and "already targets" in res["comment"]
    mod.full_upgrade()
    assert not [c for c in fake.calls if c[0] == "plan"] and ("apply", "s") in fake.calls


def test_plan_id_is_threaded_through(fake, monkeypatch):
    monkeypatch.setattr(fake, "list_plans", lambda: [{"id": "p1"}, {"id": "p2"}])
    res = mod.validate_ready(plan_id="p2")
    assert res["data"]["plan_id"] == "p2"
    assert not any("upgrade plans" in w for w in res["data"]["warnings"])
    mod.full_upgrade(plan_id="p2")
    assert ("plan", "p2", "9.1.0") in fake.calls and ("apply", "s") in fake.calls
    assert any("2 upgrade plans" in w for w in mod.validate_ready()["data"]["warnings"])


def test_report(fake):
    res = mod.report()
    assert res["changed"] is False
    assert res["data"]["available_versions"] == ["9.1.0"]
    assert len(res["data"]["components"]) == 3
