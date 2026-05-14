"""Tests for the EVC mode, hyperthreading, acceptance, and SNMP state modules."""

import pytest

from saltext.vmware.clients import vim_cluster_evc as evc_c
from saltext.vmware.clients import vim_host_acceptance as acc_c
from saltext.vmware.clients import vim_host_hyperthreading as ht_c
from saltext.vmware.clients import vim_host_snmp as snmp_c
from saltext.vmware.states import vmware_vim_cluster_evc as evc_st
from saltext.vmware.states import vmware_vim_host_acceptance as acc_st
from saltext.vmware.states import vmware_vim_host_hyperthreading as ht_st
from saltext.vmware.states import vmware_vim_host_snmp as snmp_st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (evc_st, acc_st, ht_st, snmp_st):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


# -- EVC --------------------------------------------------------------------


def test_evc_mode_already_matches(monkeypatch):
    monkeypatch.setattr(
        evc_c,
        "get",
        lambda o, cl, profile=None: {
            "enabled": True,
            "current_key": "intel-haswell",
            "supported_keys": ["intel-haswell", "intel-skylake"],
        },
    )
    ret = evc_st.mode("c1", evc_mode_key="intel-haswell")
    assert ret["changes"] == {}


def test_evc_mode_change(monkeypatch):
    calls = []
    monkeypatch.setattr(
        evc_c,
        "get",
        lambda o, cl, profile=None: {
            "current_key": "intel-haswell",
            "supported_keys": ["intel-haswell", "intel-skylake"],
        },
    )
    monkeypatch.setattr(evc_c, "configure", lambda o, cl, key, profile=None: calls.append(key))
    ret = evc_st.mode("c1", evc_mode_key="intel-skylake")
    assert ret["changes"] == {"evc": ("intel-haswell", "intel-skylake")}
    assert calls == ["intel-skylake"]


def test_evc_mode_unsupported(monkeypatch):
    monkeypatch.setattr(
        evc_c,
        "get",
        lambda o, cl, profile=None: {
            "current_key": "intel-haswell",
            "supported_keys": ["intel-haswell"],
        },
    )
    ret = evc_st.mode("c1", evc_mode_key="amd-zen3")
    assert ret["result"] is False


def test_evc_mode_disable(monkeypatch):
    calls = []
    monkeypatch.setattr(
        evc_c,
        "get",
        lambda o, cl, profile=None: {"current_key": "intel-haswell", "supported_keys": []},
    )
    monkeypatch.setattr(evc_c, "disable", lambda o, cl, profile=None: calls.append("disable"))
    ret = evc_st.mode("c1", evc_mode_key=None)
    assert calls == ["disable"]
    assert ret["changes"] == {"evc": ("intel-haswell", None)}


# -- hyperthreading ----------------------------------------------------------


def test_ht_already_matches(monkeypatch):
    monkeypatch.setattr(
        ht_c, "get", lambda o, h, profile=None: {"available": True, "active": True, "config": True}
    )
    ret = ht_st.enabled("esx-1", enabled=True)
    assert ret["changes"] == {}


def test_ht_drift_enables(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ht_c,
        "get",
        lambda o, h, profile=None: {"available": True, "active": False, "config": False},
    )
    monkeypatch.setattr(ht_c, "enable", lambda o, h, profile=None: calls.append("enable"))
    ret = ht_st.enabled("esx-1", enabled=True)
    assert calls == ["enable"]
    assert ret["changes"]["config"] == (False, True)


def test_ht_unavailable(monkeypatch):
    monkeypatch.setattr(
        ht_c,
        "get",
        lambda o, h, profile=None: {"available": False, "active": False, "config": False},
    )
    ret = ht_st.enabled("esx-1", enabled=True)
    assert ret["result"] is False


# -- acceptance --------------------------------------------------------------


def test_acceptance_already_matches(monkeypatch):
    monkeypatch.setattr(acc_c, "get", lambda o, h, profile=None: "partner")
    ret = acc_st.level("esx-1", level="partner")
    assert ret["changes"] == {}


def test_acceptance_drift(monkeypatch):
    calls = []
    monkeypatch.setattr(acc_c, "get", lambda o, h, profile=None: "community")
    monkeypatch.setattr(acc_c, "set_", lambda o, h, lvl, profile=None: calls.append(lvl))
    ret = acc_st.level("esx-1", level="partner")
    assert calls == ["partner"]
    assert ret["changes"]["level"] == ("community", "partner")


def test_acceptance_missing_level():
    ret = acc_st.level("esx-1")
    assert ret["result"] is False


# -- SNMP --------------------------------------------------------------------


def test_snmp_already_matches(monkeypatch):
    monkeypatch.setattr(
        snmp_c,
        "get",
        lambda o, h, profile=None: {
            "enabled": True,
            "port": 161,
            "read_only_communities": ["public"],
            "trap_targets": [],
        },
    )
    ret = snmp_st.config("esx-1", enabled=True, read_only_communities=["public"])
    assert ret["changes"] == {}


def test_snmp_drift(monkeypatch):
    calls = []
    monkeypatch.setattr(
        snmp_c,
        "get",
        lambda o, h, profile=None: {
            "enabled": False,
            "port": 161,
            "read_only_communities": [],
            "trap_targets": [],
        },
    )
    monkeypatch.setattr(snmp_c, "set_", lambda *a, **kw: calls.append(kw))
    ret = snmp_st.config("esx-1", enabled=True, read_only_communities=["public"])
    assert "enabled" in ret["changes"]
    assert "read_only_communities" in ret["changes"]


def test_snmp_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(
        snmp_c,
        "get",
        lambda o, h, profile=None: {
            "enabled": False,
            "port": 161,
            "read_only_communities": [],
            "trap_targets": [],
        },
    )
    monkeypatch.setattr(snmp_c, "set_", lambda *a, **kw: pytest.fail("should not write"))
    ret = snmp_st.config("esx-1", enabled=True)
    assert ret["result"] is None
