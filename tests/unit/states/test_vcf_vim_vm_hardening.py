"""Tests for states.vcf_vim_vm_hardening (912 Controls VM extraConfig)."""

import pytest

from saltext.vcf.states import vcf_vim_vm_hardening as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    """Wire __salt__ for vcf_vim_vm.get_advanced_settings and reconfigure."""
    state = {"current": {}, "calls": []}

    def _get(vm, profile=None):
        return dict(state["current"])

    def _reconfig(vm, advanced_settings=None, profile=None, **_):
        state["calls"].append(("reconfigure", vm, dict(advanced_settings or {})))
        # Simulate write so subsequent reads reflect the drift-resolved value.
        state["current"].update(advanced_settings or {})
        return "task-mo-1"

    salt = {
        "vcf_vim_vm.get_advanced_settings": _get,
        "vcf_vim_vm.reconfigure": _reconfig,
    }
    monkeypatch.setattr(st, "__salt__", salt, raising=False)
    return state


# -- console_options_locked --------------------------------------------------


def test_console_options_locked_writes_all_five_when_absent(stub):
    ret = st.console_options_locked("harden-console", vm="vm-42")
    assert ret["result"] is True
    assert len(ret["changes"]) == 5
    assert set(ret["changes"]) == set(st.CONSOLE_LOCK_KEYS)
    for key, change in ret["changes"].items():
        assert change["new"] == "TRUE"
        assert change["old"] is None
    # One reconfigure call carrying all five keys
    (call,) = stub["calls"]
    assert call[0] == "reconfigure"
    assert call[1] == "vm-42"
    assert set(call[2]) == set(st.CONSOLE_LOCK_KEYS)


def test_console_options_locked_idempotent(stub):
    stub["current"] = {k: "TRUE" for k in st.CONSOLE_LOCK_KEYS}
    ret = st.console_options_locked("harden-console", vm="vm-42")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_console_options_locked_partial_drift_writes_only_diff(stub):
    stub["current"] = {
        "isolation.tools.copy.disable": "TRUE",
        "isolation.tools.paste.disable": "TRUE",
        # Remaining three missing -> should be written
    }
    ret = st.console_options_locked("harden-console", vm="vm-42")
    assert set(ret["changes"]) == {
        "isolation.tools.setGUIOptions.enable",
        "isolation.tools.diskShrink.disable",
        "isolation.tools.diskWiper.disable",
    }
    (call,) = stub["calls"]
    assert set(call[2]) == set(ret["changes"])


def test_console_options_locked_test_mode(monkeypatch, opts, stub):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.console_options_locked("harden-console", vm="vm-42")
    assert ret["result"] is None
    assert set(ret["changes"]) == set(st.CONSOLE_LOCK_KEYS)
    assert stub["calls"] == []


# -- hgfs_disabled -----------------------------------------------------------


def test_hgfs_disabled_writes_when_absent(stub):
    ret = st.hgfs_disabled("hgfs-off", vm="vm-42")
    assert ret["result"] is True
    assert ret["changes"] == {
        "isolation.tools.hgfsServerSet.disable": {"old": None, "new": "TRUE"}
    }
    assert stub["calls"] == [
        ("reconfigure", "vm-42", {"isolation.tools.hgfsServerSet.disable": "TRUE"})
    ]


def test_hgfs_disabled_idempotent(stub):
    stub["current"] = {"isolation.tools.hgfsServerSet.disable": "TRUE"}
    ret = st.hgfs_disabled("hgfs-off", vm="vm-42")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_hgfs_disabled_test_mode(monkeypatch, opts, stub):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.hgfs_disabled("hgfs-off", vm="vm-42")
    assert ret["result"] is None
    assert stub["calls"] == []


# -- log_rotation_configured -------------------------------------------------


def test_log_rotation_writes_defaults(stub):
    ret = st.log_rotation_configured("log-rot", vm="vm-42")
    assert ret["result"] is True
    assert ret["changes"] == {
        "log.keepOld": {"old": None, "new": "10"},
        "log.rotateSize": {"old": None, "new": "1024000"},
    }
    (call,) = stub["calls"]
    assert call[2] == {"log.keepOld": "10", "log.rotateSize": "1024000"}


def test_log_rotation_custom_values(stub):
    ret = st.log_rotation_configured("log-rot", vm="vm-42", keep_old=5, rotate_size=2048000)
    assert ret["changes"]["log.keepOld"]["new"] == "5"
    assert ret["changes"]["log.rotateSize"]["new"] == "2048000"


def test_log_rotation_idempotent(stub):
    stub["current"] = {"log.keepOld": "10", "log.rotateSize": "1024000"}
    ret = st.log_rotation_configured("log-rot", vm="vm-42")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_log_rotation_partial_drift(stub):
    stub["current"] = {"log.keepOld": "10", "log.rotateSize": "500"}
    ret = st.log_rotation_configured("log-rot", vm="vm-42")
    assert set(ret["changes"]) == {"log.rotateSize"}
    (call,) = stub["calls"]
    assert call[2] == {"log.rotateSize": "1024000"}


def test_log_rotation_test_mode(monkeypatch, opts, stub):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.log_rotation_configured("log-rot", vm="vm-42")
    assert ret["result"] is None
    assert stub["calls"] == []
