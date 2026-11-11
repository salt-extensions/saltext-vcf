"""Tests for states.vcf_ops_patch."""

import pytest

from saltext.vcf.states import vcf_ops_patch as st

STATES = {
    "cluster_health_validated": "validate_cluster_health",
    "pak_downloaded": "download_pak",
    "pak_installed": "install_pak",
    "upgrade_monitored": "wait_for_upgrade",
    "cluster_online_verified": "wait_for_cluster_online",
    "full_upgrade": "full_upgrade",
    "reported": "report",
}
DRY_RUN_FUNCS = {"validate_cluster_health", "download_pak", "install_pak", "full_upgrade"}


@pytest.fixture
def salt_calls(monkeypatch):
    calls = []

    def make(func):
        def _fn(**kwargs):
            calls.append((func, kwargs))
            return {"success": True, "comment": "ok", "changed": True, "changes": {"x": 1}}

        return _fn

    monkeypatch.setattr(
        st, "__salt__", {f"vcf_ops_patch.{f}": make(f) for f in STATES.values()}, raising=False
    )
    monkeypatch.setattr(st, "__opts__", {"test": False}, raising=False)
    return calls


def test_virtual():
    assert st.__virtual__() == "vcf_ops_patch"


@pytest.mark.parametrize("state_name,func", STATES.items())
def test_state_dispatches_to_module(salt_calls, state_name, func):
    ret = getattr(st, state_name)("n", host="ops.test")
    assert ret["result"] is True
    assert ret["changes"] == {"x": 1}
    assert salt_calls[0][0] == func
    assert salt_calls[0][1]["host"] == "ops.test"
    assert ("dry_run" in salt_calls[0][1]) == (func in DRY_RUN_FUNCS)


def test_test_mode_returns_none_when_changes(salt_calls, monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.pak_installed("n")
    assert ret["result"] is None
    assert salt_calls[0][1]["dry_run"] is True


def test_unchanged_has_no_changes(monkeypatch):
    monkeypatch.setattr(
        st,
        "__salt__",
        {
            "vcf_ops_patch.report": lambda **kw: {
                "success": True,
                "comment": "c",
                "changes": {"a": 1},
            }
        },
        raising=False,
    )
    monkeypatch.setattr(st, "__opts__", {"test": False}, raising=False)
    ret = st.reported("n")
    assert ret["result"] is True
    assert ret["changes"] == {}


def test_failure_result_propagates(monkeypatch):
    monkeypatch.setattr(
        st,
        "__salt__",
        {"vcf_ops_patch.report": lambda **kw: {"success": False, "comment": "bad"}},
        raising=False,
    )
    monkeypatch.setattr(st, "__opts__", {"test": False}, raising=False)
    ret = st.reported("n")
    assert ret["result"] is False
    assert ret["comment"] == "bad"


def test_exception_becomes_failed_state(monkeypatch):
    def boom(**kw):
        raise RuntimeError("kaput")

    monkeypatch.setattr(st, "__salt__", {"vcf_ops_patch.report": boom}, raising=False)
    monkeypatch.setattr(st, "__opts__", {"test": False}, raising=False)
    ret = st.reported("n")
    assert ret["result"] is False
    assert "kaput" in ret["comment"]


@pytest.mark.parametrize("state_name", ["upgrade_monitored", "cluster_online_verified"])
def test_wait_states_skip_polling_in_test_mode(salt_calls, monkeypatch, state_name):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = getattr(st, state_name)("n")
    assert ret["result"] is None
    assert "would" in ret["comment"]
    assert salt_calls == []
