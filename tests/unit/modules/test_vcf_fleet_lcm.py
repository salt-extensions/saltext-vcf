"""Tests for modules.vcf_fleet_lcm."""

import pytest

from saltext.vcf.modules import vcf_fleet_lcm as mod


class FakeClient:
    def __init__(self, system):
        self.system = system
        self.submitted = []

    def get_system(self):
        return self.system

    available_versions = staticmethod(lambda s: ["9.1.0"])
    current_version = staticmethod(lambda s: s.get("currentVersion"))

    def select_target_version(self, system, requested=None):
        return requested or "9.1.0"

    def configure_plan(self, target):
        self.submitted.append(("plan", target))
        return "p1"

    def apply_upgrade(self, target):
        self.submitted.append(("apply", target))
        return "a1"

    def sync_depot_metadata(self):
        self.submitted.append(("sync", None))
        return "s1"

    def wait_for_task(self, task_id, *_a):
        return {"task_id": task_id, "status": "SUCCEEDED"}


@pytest.fixture
def fake(monkeypatch):
    client = FakeClient({"currentVersion": "9.0.0"})
    monkeypatch.setattr(mod, "_client", lambda **_k: client)
    return client


def test_virtual():
    assert mod.__virtual__() == "vcf_fleet_lcm"


def test_missing_host_fails(monkeypatch):
    monkeypatch.setattr(mod, "__salt__", {"pillar.get": lambda *a, **k: {}}, raising=False)
    with pytest.raises(Exception, match="host"):
        mod._client()
    with pytest.raises(Exception, match="ops_host"):
        mod._client(host="flt.example")


def test_full_upgrade_submits_plan_then_apply(fake):
    res = mod.full_upgrade()
    assert fake.submitted == [("plan", "9.1.0"), ("apply", "9.1.0")]
    assert res["changed"] and res["data"]["apply"]["task"]["status"] == "SUCCEEDED"


def test_dry_run_submits_nothing(fake):
    assert mod.apply_upgrade(dry_run=True)["changed"] is True
    assert fake.submitted == []


def test_already_at_target_is_noop(fake):
    fake.system = {"currentVersion": "9.1.0"}
    res = mod.apply_upgrade()
    assert res["changed"] is False and fake.submitted == []


def test_sync_depot_metadata_waits_for_task(fake):
    res = mod.sync_depot_metadata()
    assert fake.submitted == [("sync", None)]
    assert res["changed"] and res["data"]["task"] == {"task_id": "s1", "status": "SUCCEEDED"}


def test_sync_depot_metadata_dry_run_submits_nothing(fake):
    assert mod.sync_depot_metadata(dry_run=True)["changed"] is True
    assert fake.submitted == []
