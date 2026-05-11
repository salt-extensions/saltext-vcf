"""Tests for the DRS rule state module."""

import pytest

from saltext.vmware.clients import vim_drs_rule as c
from saltext.vmware.states import vmware_vim_drs_rule as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_vm_affinity_creates(monkeypatch):
    actions = {"created": []}
    monkeypatch.setattr(c, "get_or_none", lambda o, cl, n, profile=None: None)
    monkeypatch.setattr(
        c,
        "create_vm_affinity",
        lambda o, cl, n, vms, enabled=True, mandatory=False, profile=None: actions[
            "created"
        ].append((n, vms, enabled, mandatory)),
    )
    ret = st.vm_affinity("keep-web", cluster="domain-c9", vm_moids=["vm-1", "vm-2"])
    assert ret["changes"]["new"] == "keep-web"
    assert actions["created"][0] == ("keep-web", ["vm-1", "vm-2"], True, False)


def test_vm_anti_affinity_creates(monkeypatch):
    actions = {"created": []}
    monkeypatch.setattr(c, "get_or_none", lambda o, cl, n, profile=None: None)
    monkeypatch.setattr(
        c,
        "create_vm_anti_affinity",
        lambda o, cl, n, vms, enabled=True, mandatory=False, profile=None: actions[
            "created"
        ].append((n, vms)),
    )
    ret = st.vm_anti_affinity("split", cluster="domain-c9", vm_moids=["vm-1", "vm-2"])
    assert ret["changes"]["new"] == "split"


def test_vm_affinity_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, cl, n, profile=None: {
            "kind": "vm-affinity",
            "vm_moids": ["vm-1", "vm-2"],
            "enabled": True,
            "mandatory": False,
        },
    )
    ret = st.vm_affinity("keep", cluster="domain-c9", vm_moids=["vm-2", "vm-1"])
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]


def test_vm_affinity_updates_on_drift(monkeypatch):
    actions = {"updated": []}
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, cl, n, profile=None: {
            "kind": "vm-affinity",
            "vm_moids": ["vm-1"],
            "enabled": True,
            "mandatory": False,
        },
    )
    monkeypatch.setattr(
        c,
        "update",
        lambda o, cl, n, enabled=None, mandatory=None, vm_moids=None, profile=None: actions[
            "updated"
        ].append((n, enabled, mandatory, vm_moids)),
    )
    ret = st.vm_affinity("keep", cluster="domain-c9", vm_moids=["vm-1", "vm-2"])
    assert "vm_moids" in ret["changes"]
    assert actions["updated"][0][3] == ["vm-1", "vm-2"]


def test_vm_affinity_refuses_kind_change(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, cl, n, profile=None: {
            "kind": "vm-anti-affinity",
            "vm_moids": ["vm-1"],
            "enabled": True,
            "mandatory": False,
        },
    )
    ret = st.vm_affinity("rule", cluster="domain-c9", vm_moids=["vm-1"])
    assert ret["result"] is False
    assert "kind" in ret["comment"]


def test_absent_when_missing(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, cl, n, profile=None: None)
    ret = st.absent("keep", cluster="domain-c9")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, cl, n, profile=None: {"kind": "vm-affinity", "vm_moids": ["vm-1"]},
    )
    monkeypatch.setattr(c, "delete", lambda o, cl, n, profile=None: actions["deleted"].append(n))
    ret = st.absent("keep", cluster="domain-c9")
    assert ret["changes"] == {"deleted": "keep"}


def test_vm_affinity_test_mode(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", {**opts, "test": True}, raising=False)
    monkeypatch.setattr(c, "get_or_none", lambda o, cl, n, profile=None: None)
    ret = st.vm_affinity("keep", cluster="domain-c9", vm_moids=["vm-1"])
    assert ret["result"] is None
    assert "would be created" in ret["comment"]
