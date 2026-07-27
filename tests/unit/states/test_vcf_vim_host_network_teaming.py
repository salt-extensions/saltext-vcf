"""Tests for the vswitch_teaming_configured state (physical-uplink failover mode)."""

import pytest

from saltext.vcf.clients import vim_host_network as c
from saltext.vcf.states import vcf_vim_host_network as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_teaming_missing_vswitch(monkeypatch):
    monkeypatch.setattr(c, "vswitch_get_or_none", lambda o, h, n, profile=None: None)
    ret = st.vswitch_teaming_configured("vSwitch0", host="esxi-01", policy="loadbalance_srcid")
    assert ret["result"] is False
    assert "not found" in ret["comment"]


def test_teaming_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "vswitch_get_or_none",
        lambda o, h, n, profile=None: {
            "name": n,
            "teaming": {
                "policy": "loadbalance_srcid",
                "notify_switches": True,
                "active_nic": ["vmnic0", "vmnic1"],
                "standby_nic": [],
            },
        },
    )
    ret = st.vswitch_teaming_configured(
        "vSwitch0",
        host="esxi-01",
        policy="loadbalance_srcid",
        notify_switches=True,
        active_nic=["vmnic0", "vmnic1"],
        standby_nic=[],
    )
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]


def test_teaming_updates_on_drift(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(
        c,
        "vswitch_get_or_none",
        lambda o, h, n, profile=None: {
            "name": n,
            "teaming": {"policy": "loadbalance_srcid", "notify_switches": False},
        },
    )
    monkeypatch.setattr(
        c,
        "vswitch_set_teaming",
        lambda o, h, n, **kw: actions["set"].append((h, n, kw)),
    )
    ret = st.vswitch_teaming_configured(
        "vSwitch0",
        host="esxi-01",
        policy="failover_explicit",
        notify_switches=True,
    )
    assert ret["changes"]["policy"] == ("loadbalance_srcid", "failover_explicit")
    assert ret["changes"]["notify_switches"] == (False, True)
    assert actions["set"][0][2]["policy"] == "failover_explicit"


def test_teaming_test_mode(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", {**opts, "test": True}, raising=False)
    monkeypatch.setattr(
        c,
        "vswitch_get_or_none",
        lambda o, h, n, profile=None: {"name": n, "teaming": {"policy": "loadbalance_srcid"}},
    )
    ret = st.vswitch_teaming_configured("vSwitch0", host="esxi-01", policy="failover_explicit")
    assert ret["result"] is None
    assert "would be updated" in ret["comment"]


def test_teaming_ignores_none_fields(monkeypatch):
    """Fields the caller didn't set must not trigger drift."""
    monkeypatch.setattr(
        c,
        "vswitch_get_or_none",
        lambda o, h, n, profile=None: {
            "name": n,
            "teaming": {
                "policy": "loadbalance_srcid",
                "notify_switches": True,
                "active_nic": ["vmnic0"],
                "standby_nic": ["vmnic1"],  # would drift if checked
            },
        },
    )
    ret = st.vswitch_teaming_configured("vSwitch0", host="esxi-01", policy="loadbalance_srcid")
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]
