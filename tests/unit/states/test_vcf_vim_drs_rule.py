"""Tests for the DRS rule state module."""

import pytest

from saltext.vcf.clients import vim_drs_rule as c
from saltext.vcf.states import vcf_vim_drs_rule as st


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


# -- VM/host group state ----------------------------------------------------


def test_vm_group_creates_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_group_or_none", lambda o, cl, n, profile=None: None)
    monkeypatch.setattr(
        c, "create_vm_group", lambda o, cl, n, vms, profile=None: calls.append((n, vms))
    )
    ret = st.vm_group("prod-vms", cluster="domain-c9", vm_moids=["vm-1", "vm-2"])
    assert ret["changes"]["new"] == "prod-vms"
    assert calls[0] == ("prod-vms", ["vm-1", "vm-2"])


def test_vm_group_idempotent(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_group_or_none",
        lambda o, cl, n, profile=None: {"kind": "vm", "members": ["vm-1", "vm-2"]},
    )
    monkeypatch.setattr(c, "update_group", lambda *a, **kw: pytest.fail("should not update"))
    monkeypatch.setattr(c, "create_vm_group", lambda *a, **kw: pytest.fail("should not create"))
    ret = st.vm_group("prod-vms", cluster="domain-c9", vm_moids=["vm-1", "vm-2"])
    assert ret["changes"] == {}


def test_vm_group_drift_replaces_members(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "get_group_or_none",
        lambda o, cl, n, profile=None: {"kind": "vm", "members": ["vm-1"]},
    )
    monkeypatch.setattr(
        c,
        "update_group",
        lambda o, cl, n, vm_moids=None, host_moids=None, profile=None: calls.append((n, vm_moids)),
    )
    ret = st.vm_group("prod-vms", cluster="domain-c9", vm_moids=["vm-1", "vm-2"])
    assert ret["changes"]["members"] == (["vm-1"], ["vm-1", "vm-2"])
    assert calls[0] == ("prod-vms", ["vm-1", "vm-2"])


def test_host_group_kind_mismatch(monkeypatch):
    monkeypatch.setattr(
        c, "get_group_or_none", lambda o, cl, n, profile=None: {"kind": "vm", "members": []}
    )
    ret = st.host_group("name", cluster="domain-c9", host_moids=["h-1"])
    assert ret["result"] is False


def test_group_absent_idempotent(monkeypatch):
    monkeypatch.setattr(c, "get_group_or_none", lambda o, cl, n, profile=None: None)
    ret = st.group_absent("missing", cluster="domain-c9")
    assert ret["changes"] == {}


def test_group_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "get_group_or_none", lambda o, cl, n, profile=None: {"kind": "vm", "members": []}
    )
    monkeypatch.setattr(c, "delete_group", lambda o, cl, n, profile=None: calls.append(n))
    ret = st.group_absent("prod-vms", cluster="domain-c9")
    assert ret["changes"]["deleted"] == "prod-vms"


# -- VM-Host rule state -----------------------------------------------------


def test_vm_host_creates(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, cl, n, profile=None: None)
    monkeypatch.setattr(
        c,
        "create_vm_host",
        lambda o, cl, n, vmg, hg, affine=True, enabled=True, mandatory=False, profile=None: calls.append(
            (n, vmg, hg, affine)
        ),
    )
    ret = st.vm_host(
        "pin-prod", cluster="domain-c9", vm_group_name="prod-vms", host_group_name="prod-hosts"
    )
    assert ret["changes"]["new"] == "pin-prod"
    assert calls[0] == ("pin-prod", "prod-vms", "prod-hosts", True)


def test_vm_host_idempotent(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, cl, n, profile=None: {
            "kind": "vm-host",
            "vm_group_name": "prod-vms",
            "affine_host_group_name": "prod-hosts",
            "anti_affine_host_group_name": None,
            "enabled": True,
            "mandatory": False,
        },
    )
    monkeypatch.setattr(c, "delete", lambda *a, **kw: pytest.fail("no-op expected"))
    ret = st.vm_host(
        "pin", cluster="domain-c9", vm_group_name="prod-vms", host_group_name="prod-hosts"
    )
    assert ret["changes"] == {}


def test_vm_host_drift_recreates(monkeypatch):
    deleted = []
    created = []
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, cl, n, profile=None: {
            "kind": "vm-host",
            "vm_group_name": "prod-vms",
            "affine_host_group_name": "old-hosts",
            "anti_affine_host_group_name": None,
            "enabled": True,
            "mandatory": False,
        },
    )
    monkeypatch.setattr(c, "delete", lambda o, cl, n, profile=None: deleted.append(n))
    monkeypatch.setattr(
        c,
        "create_vm_host",
        lambda o, cl, n, vmg, hg, affine=True, enabled=True, mandatory=False, profile=None: created.append(
            hg
        ),
    )
    ret = st.vm_host(
        "pin", cluster="domain-c9", vm_group_name="prod-vms", host_group_name="new-hosts"
    )
    assert deleted == ["pin"]
    assert created == ["new-hosts"]
    assert "host_group_name" in ret["changes"]
