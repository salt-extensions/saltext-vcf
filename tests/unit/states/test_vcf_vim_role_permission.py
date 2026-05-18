"""Tests for the role + permission state modules."""

import pytest

from saltext.vcf.clients import vim_permission as perm_c
from saltext.vcf.clients import vim_role as role_c
from saltext.vcf.states import vcf_vim_permission as perm_state
from saltext.vcf.states import vcf_vim_role as role_state


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (role_state, perm_state):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


# ---------- role state ----------


def test_role_present_creates_when_missing(monkeypatch):
    actions = {"created": [], "updated": []}
    monkeypatch.setattr(role_c, "get_or_none", lambda o, n, profile=None: None)
    monkeypatch.setattr(
        role_c,
        "create",
        lambda o, n, p, profile=None: actions["created"].append((n, p)) or 99,
    )
    ret = role_state.present("MyRole", privileges=["System.View", "System.Read"])
    assert ret["changes"]["new"] == "MyRole"
    assert actions["created"][0] == ("MyRole", ["System.Read", "System.View"])


def test_role_present_already_matches(monkeypatch):
    monkeypatch.setattr(
        role_c,
        "get_or_none",
        lambda o, n, profile=None: {
            "name": n,
            "system": False,
            "privilege": ["System.View", "System.Read"],
        },
    )
    ret = role_state.present("MyRole", privileges=["System.Read", "System.View"])
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]


def test_role_present_updates_on_drift(monkeypatch):
    actions = {"updated": []}
    monkeypatch.setattr(
        role_c,
        "get_or_none",
        lambda o, n, profile=None: {
            "name": n,
            "system": False,
            "privilege": ["System.View"],
        },
    )
    monkeypatch.setattr(
        role_c,
        "update",
        lambda o, n, p, profile=None: actions["updated"].append((n, p)),
    )
    ret = role_state.present("MyRole", privileges=["System.View", "System.Read"])
    assert ret["changes"]["added"] == ["System.Read"]
    assert ret["changes"]["removed"] == []
    assert actions["updated"][0][1] == ["System.Read", "System.View"]


def test_role_present_refuses_system_role(monkeypatch):
    monkeypatch.setattr(
        role_c,
        "get_or_none",
        lambda o, n, profile=None: {"name": n, "system": True, "privilege": []},
    )
    ret = role_state.present("Admin", privileges=["System.View"])
    assert ret["changes"] == {}
    assert "system-defined" in ret["comment"]


def test_role_absent_when_missing(monkeypatch):
    monkeypatch.setattr(role_c, "get_or_none", lambda o, n, profile=None: None)
    ret = role_state.absent("MyRole")
    assert ret["changes"] == {}


def test_role_absent_deletes_custom(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(
        role_c,
        "get_or_none",
        lambda o, n, profile=None: {"name": n, "system": False, "privilege": []},
    )
    monkeypatch.setattr(
        role_c,
        "delete",
        lambda o, n, fail_if_used=True, profile=None: actions["deleted"].append(n),
    )
    ret = role_state.absent("MyRole")
    assert ret["changes"] == {"deleted": "MyRole"}


def test_role_absent_refuses_system_role(monkeypatch):
    monkeypatch.setattr(
        role_c,
        "get_or_none",
        lambda o, n, profile=None: {"name": n, "system": True, "privilege": []},
    )
    ret = role_state.absent("Admin")
    assert ret["changes"] == {}
    assert "system-defined" in ret["comment"]


def test_role_present_test_mode(monkeypatch, opts):
    monkeypatch.setattr(role_state, "__opts__", {**opts, "test": True}, raising=False)
    monkeypatch.setattr(role_c, "get_or_none", lambda o, n, profile=None: None)
    ret = role_state.present("MyRole", privileges=["System.View"])
    assert ret["result"] is None
    assert "would be created" in ret["comment"]


# ---------- permission state ----------


def test_permission_present_creates_when_missing(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(perm_c, "list_", lambda o, e, inherited=False, profile=None: [])
    monkeypatch.setattr(
        perm_c,
        "set_",
        lambda o, e, p, r, propagate=True, group=False, profile=None: actions["set"].append(
            (e, p, r, propagate, group)
        ),
    )
    ret = perm_state.present("alice on vm-100", "vm-100", "alice@vsphere.local", "Admin")
    assert ret["changes"]["new"]["role"] == "Admin"
    assert actions["set"][0] == ("vm-100", "alice@vsphere.local", "Admin", True, False)


def test_permission_present_already_matches(monkeypatch):
    monkeypatch.setattr(
        perm_c,
        "list_",
        lambda o, e, inherited=False, profile=None: [
            {
                "principal": "alice@vsphere.local",
                "group": False,
                "role": "Admin",
                "propagate": True,
            }
        ],
    )
    ret = perm_state.present("alice on vm-100", "vm-100", "alice@vsphere.local", "Admin")
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]


def test_permission_present_changes_role(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(
        perm_c,
        "list_",
        lambda o, e, inherited=False, profile=None: [
            {
                "principal": "alice@vsphere.local",
                "group": False,
                "role": "ReadOnly",
                "propagate": True,
            }
        ],
    )
    monkeypatch.setattr(
        perm_c,
        "set_",
        lambda o, e, p, r, propagate=True, group=False, profile=None: actions["set"].append(
            (e, p, r, propagate)
        ),
    )
    ret = perm_state.present("alice on vm-100", "vm-100", "alice@vsphere.local", "Admin")
    assert ret["changes"]["role"] == ("ReadOnly", "Admin")


def test_permission_absent_when_missing(monkeypatch):
    monkeypatch.setattr(perm_c, "list_", lambda o, e, inherited=False, profile=None: [])
    ret = perm_state.absent("alice on vm-100", "vm-100", "alice@vsphere.local")
    assert ret["changes"] == {}


def test_permission_absent_removes(monkeypatch):
    actions = {"removed": []}
    monkeypatch.setattr(
        perm_c,
        "list_",
        lambda o, e, inherited=False, profile=None: [
            {
                "principal": "alice@vsphere.local",
                "group": False,
                "role": "Admin",
                "propagate": True,
            }
        ],
    )
    monkeypatch.setattr(
        perm_c,
        "remove",
        lambda o, e, p, group=False, profile=None: actions["removed"].append((e, p)),
    )
    ret = perm_state.absent("alice on vm-100", "vm-100", "alice@vsphere.local")
    assert ret["changes"]["removed"]["principal"] == "alice@vsphere.local"
