"""Tests for the cluster DRS/HA/EVC state module."""

import pytest

from saltext.vmware.clients import vim_cluster_config as c
from saltext.vmware.states import vmware_vim_cluster_config as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_drs_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "drs_get",
        lambda o, cl, profile=None: {
            "enabled": True,
            "default_vm_behavior": "fullyAutomated",
            "migration_threshold": 3,
            "vm_monitoring_enabled": False,
        },
    )
    ret = st.drs(
        "domain-c9",
        enabled=True,
        default_vm_behavior="fullyAutomated",
        migration_threshold=3,
    )
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]


def test_drs_updates_on_drift(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(
        c,
        "drs_get",
        lambda o, cl, profile=None: {
            "enabled": False,
            "default_vm_behavior": "manual",
            "migration_threshold": 3,
            "vm_monitoring_enabled": False,
        },
    )
    monkeypatch.setattr(
        c,
        "drs_set",
        lambda o, cl, profile=None, **kw: actions["set"].append(kw),
    )
    ret = st.drs("domain-c9", enabled=True, default_vm_behavior="fullyAutomated")
    assert "enabled" in ret["changes"]
    assert "default_vm_behavior" in ret["changes"]
    assert "migration_threshold" not in ret["changes"]  # wasn't passed
    assert actions["set"][0] == {"enabled": True, "default_vm_behavior": "fullyAutomated"}


def test_ha_updates_on_drift(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(
        c,
        "ha_get",
        lambda o, cl, profile=None: {
            "enabled": False,
            "host_monitoring": "disabled",
            "vm_monitoring": "vmMonitoringDisabled",
            "restart_priority": "medium",
            "isolation_response": "none",
            "admission_control_enabled": False,
        },
    )
    monkeypatch.setattr(
        c,
        "ha_set",
        lambda o, cl, profile=None, **kw: actions["set"].append(kw),
    )
    ret = st.ha(
        "domain-c9",
        enabled=True,
        vm_monitoring="vmMonitoringOnly",
        restart_priority="high",
    )
    assert "enabled" in ret["changes"]
    assert "vm_monitoring" in ret["changes"]
    assert actions["set"][0]["vm_monitoring"] == "vmMonitoringOnly"


def test_evc_already_at_mode(monkeypatch):
    monkeypatch.setattr(c, "evc_get", lambda o, cl, profile=None: {"current_mode": "intel-skylake"})
    ret = st.evc("domain-c9", mode="intel-skylake")
    assert ret["changes"] == {}


def test_evc_changes_mode(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(
        c, "evc_get", lambda o, cl, profile=None: {"current_mode": "intel-broadwell"}
    )
    monkeypatch.setattr(
        c,
        "evc_set",
        lambda o, cl, mode, profile=None: actions["set"].append((cl, mode)),
    )
    ret = st.evc("domain-c9", mode="intel-skylake")
    assert ret["changes"]["mode"] == ("intel-broadwell", "intel-skylake")
    assert actions["set"][0] == ("domain-c9", "intel-skylake")


def test_evc_disables_when_mode_none(monkeypatch):
    actions = {"disabled": []}
    monkeypatch.setattr(c, "evc_get", lambda o, cl, profile=None: {"current_mode": "intel-skylake"})
    monkeypatch.setattr(
        c, "evc_disable", lambda o, cl, profile=None: actions["disabled"].append(cl)
    )
    st.evc("domain-c9", mode=None)
    assert actions["disabled"] == ["domain-c9"]


def test_drs_test_mode(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", {**opts, "test": True}, raising=False)
    monkeypatch.setattr(
        c,
        "drs_get",
        lambda o, cl, profile=None: {
            "enabled": False,
            "default_vm_behavior": "manual",
            "migration_threshold": 3,
            "vm_monitoring_enabled": False,
        },
    )
    ret = st.drs("domain-c9", enabled=True)
    assert ret["result"] is None
    assert "would be updated" in ret["comment"]
