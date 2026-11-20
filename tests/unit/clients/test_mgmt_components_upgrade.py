"""Tests for clients.mgmt_components_upgrade."""

import pytest

from saltext.vcf.clients.fleet_lcm import FleetLcmError
from saltext.vcf.clients.mgmt_components_upgrade import MgmtComponentsUpgradeClient

RELEASES = [
    {
        "version": "9.1.0",
        "components": [
            {"type": "VSP", "versions": ["2.0", "1.9"]},
            {"type": "OPS", "versions": ["9.1.0"]},
            {"type": "EMPTY", "versions": []},
        ],
    },
    {"targetVersion": "9.0.2", "components": [{"type": "VSP", "versions": ["1.8"]}]},
]


@pytest.fixture
def client():
    return MgmtComponentsUpgradeClient("flt.example", "ops.example", "u", "p")


def _respond(client, monkeypatch, payload):
    calls = []
    monkeypatch.setattr(client, "request", lambda m, p, b=None: calls.append((m, p, b)) or payload)
    return calls


PLANS = [
    {"id": "old", "status": "READY", "updateTime": "2026-11-16T19:00:00Z"},
    {"id": "new", "status": "READY", "updateTime": "2026-11-16T20:00:00Z"},
    {"id": "busy", "status": "RUNNING", "updateTime": "2026-11-17T00:00:00Z"},
]


def test_select_plan_prefers_newest_ready_and_warns(client):
    plan, warnings = client.select_plan(PLANS)
    assert plan["id"] == "new" and len(warnings) == 1 and "plan_id" in warnings[0]
    assert client.select_plan(PLANS, "old") == (PLANS[0], [])
    assert client.select_plan([PLANS[2]])[0]["id"] == "busy"
    assert client.select_plan([PLANS[0]]) == (PLANS[0], [])
    with pytest.raises(FleetLcmError, match="not found.*old, new, busy"):
        client.select_plan(PLANS, "zzz")
    with pytest.raises(FleetLcmError, match="upgrade plan"):
        client.select_plan([])


def test_plan_id_from_elements_or_list(client, monkeypatch):
    _respond(client, monkeypatch, {"elements": [{"id": "plan1"}]})
    assert client.get_upgrade_plan_id() == "plan1"
    _respond(client, monkeypatch, [{"id": "plan2"}])
    assert client.get_upgrade_plan_id() == "plan2"
    _respond(client, monkeypatch, {"elements": []})
    with pytest.raises(FleetLcmError, match="upgrade plan"):
        client.get_upgrade_plan_id()


def test_list_and_select_release(client, monkeypatch):
    _respond(client, monkeypatch, {"elements": RELEASES + [{"components": []}]})
    releases = client.list_releases()
    assert len(releases) == 2
    assert client.select_release(releases)["version"] == "9.1.0"
    assert client.select_release(releases, "9.0.2")["targetVersion"] == "9.0.2"
    with pytest.raises(FleetLcmError, match="not available.*9.1.0, 9.0.2"):
        client.select_release(releases, "8.0")
    with pytest.raises(FleetLcmError, match="depot"):
        client.select_release([])


def test_desired_state_takes_newest_version_per_component(client):
    assert client.desired_state(RELEASES[0]) == {
        "spec": {
            "desiredSoftware": {
                "version": "9.1.0",
                "components": [
                    {"type": "VSP", "version": "2.0"},
                    {"type": "OPS", "version": "9.1.0"},
                ],
            }
        }
    }
    with pytest.raises(FleetLcmError, match="no component versions"):
        client.desired_state({"version": "9.2", "components": []})


def test_desired_state_sends_only_release_components(client):
    comps = client.desired_state(RELEASES[0])["spec"]["desiredSoftware"]["components"]
    assert [c["type"] for c in comps] == ["VSP", "OPS"]


def test_plan_matches(client):
    desired = client.desired_state(RELEASES[0])
    plan = {
        "spec": {
            "desiredSoftware": {
                "version": "9.1.0",
                "components": [
                    {"type": "vsp", "version": "2.0"},
                    {"type": "OPS", "version": "9.1.0"},
                    {"type": "EXTRA", "version": "1"},  # extras in the plan do not matter
                ],
            }
        }
    }
    assert client.plan_matches(plan, desired) is True
    plan["spec"]["desiredSoftware"]["components"][0]["version"] = "1.9"
    assert client.plan_matches(plan, desired) is False
    plan["spec"]["desiredSoftware"]["components"][0]["version"] = "2.0"
    plan["spec"]["desiredSoftware"]["version"] = "9.0.0"
    assert client.plan_matches(plan, desired) is False
    assert client.plan_matches({}, desired) is False


def test_set_desired_state_ignores_a_plan_shaped_response(client, monkeypatch):
    """PATCH answers with the updated plan: its id is the plan id, never a task id."""
    _respond(
        client,
        monkeypatch,
        {"id": "plan-uuid", "spec": {"desiredSoftware": {}}, "status": "SYNCING"},
    )
    assert client.set_desired_state("plan-uuid", {"spec": {}}) is None


def test_wait_for_plan_ready_waits_for_sync_and_matching_spec(client, monkeypatch):
    desired = client.desired_state(RELEASES[0])
    want = desired["spec"]["desiredSoftware"]
    stale = {"status": "READY", "spec": {"desiredSoftware": {"version": "9.0.0", "components": []}}}
    synced = {"status": "SYNCING", "spec": {"desiredSoftware": want}}
    ready = {"status": "READY", "spec": {"desiredSoftware": want}}
    seq = [stale, synced, FleetLcmError("blip"), ready]
    monkeypatch.setattr(client, "request", lambda m, p, b=None: _next(seq))
    waits = []
    assert client.wait_for_plan_ready("p", desired, sleep=waits.append)["status"] == "READY"
    assert len(waits) == 3


def _next(seq):
    item = seq.pop(0)
    if isinstance(item, Exception):
        raise item
    return item


def test_wait_for_plan_ready_times_out_with_the_last_status(client, monkeypatch):
    desired = client.desired_state(RELEASES[0])
    monkeypatch.setattr(client, "request", lambda m, p, b=None: {"status": "SYNCING", "spec": {}})
    with pytest.raises(FleetLcmError, match="did not become READY.*last status SYNCING"):
        client.wait_for_plan_ready("p", desired, timeout_seconds=0, sleep=lambda _s: None)


def test_set_desired_state_patches_and_tolerates_no_task(client, monkeypatch):
    calls = _respond(client, monkeypatch, None)
    assert client.set_desired_state("p", {"spec": {}}) is None
    assert calls == [("PATCH", "/fleet-lcm/v1/upgrade-plans/p", {"spec": {}})]
    _respond(client, monkeypatch, {"id": "t1"})
    assert client.set_desired_state("p", {}) == "t1"


RELEASE = {
    "version": "9.1.0",
    "components": [
        {"type": "VSP", "versions": ["2.0"]},
        {"type": "VCF_SDDC_LCM", "versions": ["9.1.0"]},
        {"type": "VCF_FLEET_DEPOT", "versions": ["9.1.0"]},
        {"type": "OPS", "versions": ["9.1.0"]},
        {"type": "VCD_MIGRATOR", "versions": ["9.1.0"]},
    ],
}
INVENTORY = [
    {"id": "d", "componentType": "VCF_FLEET_DEPOT", "fqdn": "depot", "currentVersion": "9.0.0"},
    {"id": "v", "componentType": "vsp", "fqdn": "vsp1", "version": "1.0"},
    {"id": "o", "componentType": "ops", "fqdn": "ops", "currentVersion": "9.0.0"},
    {"id": "s", "componentType": "VCF_SDDC_LCM", "fqdn": "sddc"},
    {"id": "x", "componentType": "UNLISTED"},
]


def test_list_components_accepts_components_wrapper(client, monkeypatch):
    _respond(client, monkeypatch, {"components": [{"id": "a", "componentType": "OPS"}, "junk"]})
    assert client.list_components() == [{"id": "a", "componentType": "OPS"}]
    _respond(client, monkeypatch, {"elements": [{"id": "b"}]})
    assert client.list_components() == [{"id": "b"}]
    _respond(client, monkeypatch, {})
    assert client.list_components() == []


def test_queue_follows_mandatory_order_not_inventory_order(client):
    queue, warnings = client.build_queue(INVENTORY, RELEASE)
    assert [q["id"] for q in queue] == ["s", "o", "v", "d"]
    assert queue[2]["current"] == "1.0" and queue[2]["desired"] == "2.0"
    # Types not deployed (or not in the release) are skipped with a warning, never reordered.
    assert len(warnings) == 8 and any("VCF Automation" in w for w in warnings)


def test_deployed_release_component_missing_from_order_is_warned(client):
    release = {
        **RELEASE,
        "components": RELEASE["components"] + [{"type": "VCF_OPS_CLOUD_PROXY", "versions": ["1"]}],
    }
    comps = INVENTORY + [
        {"id": "m", "componentType": "VCD_MIGRATOR"},
        {"id": "cp", "componentType": "VCF_OPS_CLOUD_PROXY"},
    ]
    queue, warnings = client.build_queue(comps, release)
    assert not any("CLOUD_PROXY" in w for w in warnings)  # part of OPS: ignored, not warned
    assert "m" not in [q["id"] for q in queue]
    assert any("VCD_MIGRATOR" in w and "NOT be upgraded" in w for w in warnings)


def test_queue_custom_order_and_multiple_instances(client):
    comps = [{"id": "a", "componentType": "VSP"}, {"id": "b", "componentType": "VSP"}]
    queue, _ = client.build_queue(comps, RELEASE, order=[("VSP", "VSP")])
    assert [q["id"] for q in queue] == ["a", "b"]


def test_queue_skips_type_missing_from_release(client):
    comps = [{"id": "a", "componentType": "OPS_LOGS"}, {"id": "s", "componentType": "VCF_SDDC_LCM"}]
    queue, warnings = client.build_queue(comps, RELEASE)
    assert [q["id"] for q in queue] == ["s"]
    assert any("no version for LOGS" in w for w in warnings)


def test_queue_errors_when_nothing_matches(client):
    with pytest.raises(FleetLcmError, match="Inventory types: ODD"):
        client.build_queue([{"id": "a", "componentType": "ODD"}], RELEASE)


@pytest.mark.parametrize("action", ["precheck", "apply"])
def test_plan_actions_scope_to_component(client, monkeypatch, action):
    calls = _respond(client, monkeypatch, {"id": "t1"})
    assert getattr(client, action)("p", "c1") == "t1"
    assert calls == [
        (
            "POST",
            f"/fleet-lcm/v1/upgrade-plans/p?action={action}",
            {"componentsFilter": [{"id": "c1"}]},
        )
    ]


def test_plan_action_requires_task_id(client, monkeypatch):
    _respond(client, monkeypatch, {})
    with pytest.raises(FleetLcmError, match="no task id"):
        client.precheck("p", "c1")


def _tasks(client, monkeypatch, tasks):
    monkeypatch.setattr(client, "request", lambda m, p, b=None: {"elements": list(tasks)})


def test_running_workflows_only_counts_running_precheck_and_apply(client, monkeypatch):
    _tasks(
        client,
        monkeypatch,
        [
            {"status": "RUNNING", "type": "APPLY", "resourceType": "OPS"},
            {"status": "SUCCEEDED", "type": "APPLY"},
            {"status": "RUNNING", "type": "OTHER"},
            {"status": "PENDING", "type": "PRECHECK", "resourceType": "VSP"},
        ],
    )
    assert [t["resourceType"] for t in client.running_workflows()] == ["OPS", "VSP"]


def test_assert_scope_passes_for_a_single_component(client, monkeypatch):
    _tasks(
        client,
        monkeypatch,
        [{"parentTaskId": "P", "resourceId": "c1"}, {"parentTaskId": "X", "resourceId": "z"}],
    )
    client.assert_scope("P", "c1", sleep=lambda _s: None)


def test_assert_scope_aborts_when_other_components_are_covered(client, monkeypatch):
    _tasks(
        client,
        monkeypatch,
        [
            {"parentTaskId": "P", "resourceId": "c1", "resourceType": "VCF_SDDC_LCM"},
            {"parentTaskId": "P", "resourceId": "c2", "resourceType": "OPS"},
            {"parentTaskId": "P", "resourceId": "c3", "resourceType": "VSP"},
        ],
    )
    with pytest.raises(FleetLcmError, match="not honored.*OPS, VSP|OPS, VSP.*not honored"):
        client.assert_scope("P", "c1", sleep=lambda _s: None)


def test_assert_scope_fails_closed_without_children(client, monkeypatch):
    _tasks(client, monkeypatch, [])
    waits = []
    with pytest.raises(FleetLcmError, match="Cannot verify"):
        client.assert_scope("P", "c1", sleep=waits.append)
    assert len(waits) == 3


def test_get_plan_components_keyed_by_id_and_scoped_by_query(client, monkeypatch):
    calls = _respond(
        client,
        monkeypatch,
        {
            "components": {
                "elements": [
                    {"id": "a", "status": "ELIGIBLE"},
                    {"id": "b", "status": "ON_TARGET"},
                    "junk",
                ]
            }
        },
    )
    got = client.get_plan_components("p1", "a")
    assert sorted(got) == ["a", "b"] and got["b"]["status"] == "ON_TARGET"
    assert (
        calls[0][1]
        == "/fleet-lcm/v1/upgrade-plans/p1?includeAllComponents=true&componentsPageSize=200&componentId=a"
    )
    _respond(client, monkeypatch, {})
    assert client.get_plan_components("p1") == {}


def test_component_problem_explains_status_messages_and_dependencies(client):
    text = client.component_problem(
        {
            "status": "INELIGIBLE",
            "dependsOn": ["OPS"],
            "messages": [
                {"level": "ERROR", "message": {"defaultMessage": "OPS must be upgraded first"}}
            ],
        }
    )
    assert text == "status INELIGIBLE; ERROR: OPS must be upgraded first; depends on OPS"
    assert client.component_problem({"status": "PENDING"}) == "status PENDING"
