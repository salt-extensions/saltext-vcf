"""Tests for states.vcf_fleet_lcm."""

import pytest

from saltext.vcf.states import vcf_fleet_lcm as st

STATES = {
    "ready_validated": "validate_ready",
    "plan_configured": "configure_plan",
    "upgrade_applied": "apply_upgrade",
    "full_upgrade": "full_upgrade",
    "depot_synced": "sync_depot_metadata",
    "reported": "report",
}


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def make(func):
        def _fn(**kwargs):
            seen.append((func, kwargs))
            return {"success": True, "comment": "ok", "changed": True, "changes": {"x": 1}}

        return _fn

    monkeypatch.setattr(
        st, "__salt__", {f"vcf_fleet_lcm.{f}": make(f) for f in STATES.values()}, raising=False
    )
    monkeypatch.setattr(st, "__opts__", {"test": False}, raising=False)
    return seen


def test_virtual():
    assert st.__virtual__() == "vcf_fleet_lcm"


@pytest.mark.parametrize("state,func", STATES.items())
def test_state_calls_module(calls, state, func):
    ret = getattr(st, state)("n", host="h")
    assert ret["result"] is True and ret["changes"] == {"x": 1}
    assert calls[0][0] == func


def test_test_mode_returns_none_and_passes_dry_run(calls, monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    assert st.upgrade_applied("n")["result"] is None
    assert calls[0][1]["dry_run"] is True


def test_exception_fails_state(monkeypatch):
    def boom(**_k):
        raise RuntimeError("bad")

    monkeypatch.setattr(st, "__salt__", {"vcf_fleet_lcm.report": boom}, raising=False)
    monkeypatch.setattr(st, "__opts__", {"test": False}, raising=False)
    ret = st.reported("n")
    assert ret["result"] is False and "bad" in ret["comment"]
