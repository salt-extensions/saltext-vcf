"""Tests for VCF Ops state modules (credential, user, role, supermetric)."""

import pytest

from saltext.vcf.clients import vcfops_auth as auth_c
from saltext.vcf.clients import vcfops_credential as cred_c
from saltext.vcf.clients import vcfops_supermetric as sm_c
from saltext.vcf.states import vcf_vcfops_credential as cred_state
from saltext.vcf.states import vcf_vcfops_role as role_state
from saltext.vcf.states import vcf_vcfops_supermetric as sm_state
from saltext.vcf.states import vcf_vcfops_user as user_state


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (cred_state, role_state, user_state, sm_state):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_credential_present_creates(monkeypatch):
    actions = {"created": [], "deleted": []}
    monkeypatch.setattr(cred_c, "list_", lambda o, profile=None: {"credentialInstances": []})
    monkeypatch.setattr(
        cred_c, "create", lambda o, spec, profile=None: actions["created"].append(spec)
    )
    monkeypatch.setattr(
        cred_c, "delete", lambda o, cid, profile=None: actions["deleted"].append(cid)
    )
    ret = cred_state.present(
        "vc-prod", "VMWARE", "PRINCIPALCREDENTIAL", [{"name": "USER", "value": "u"}]
    )
    assert ret["changes"] == {"new": "vc-prod"}
    assert actions["created"][0]["name"] == "vc-prod"


def test_credential_present_already_exists(monkeypatch):
    monkeypatch.setattr(
        cred_c,
        "list_",
        lambda o, profile=None: {
            "credentialInstances": [
                {
                    "id": "1",
                    "name": "vc-prod",
                    "adapterKindKey": "VMWARE",
                    "credentialKindKey": "PRINCIPALCREDENTIAL",
                }
            ]
        },
    )
    ret = cred_state.present("vc-prod", "VMWARE", "PRINCIPALCREDENTIAL", [])
    assert ret["changes"] == {}


def test_credential_absent_deletes_by_lookup(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(
        cred_c,
        "list_",
        lambda o, profile=None: {
            "credentialInstances": [
                {
                    "id": "1",
                    "name": "vc-prod",
                    "adapterKindKey": "VMWARE",
                    "credentialKindKey": "PRINCIPALCREDENTIAL",
                }
            ]
        },
    )
    monkeypatch.setattr(
        cred_c, "delete", lambda o, cid, profile=None: actions["deleted"].append(cid)
    )
    ret = cred_state.absent("vc-prod", "VMWARE", "PRINCIPALCREDENTIAL")
    assert ret["changes"] == {"deleted": "vc-prod"}
    assert actions["deleted"] == ["1"]


def test_user_present_creates(monkeypatch):
    actions = {"created": []}
    monkeypatch.setattr(auth_c, "users_list", lambda o, profile=None: {"users": []})
    monkeypatch.setattr(
        auth_c,
        "users_create",
        lambda o, spec, profile=None: actions["created"].append(spec),
    )
    ret = user_state.present("alice", password="p", first_name="A", role_names=["Admin"])
    assert ret["changes"] == {"new": "alice"}
    assert actions["created"][0]["roleNames"] == ["Admin"]
    assert actions["created"][0]["password"] == "p"


def test_user_present_already(monkeypatch):
    monkeypatch.setattr(
        auth_c,
        "users_list",
        lambda o, profile=None: {"users": [{"id": "u-1", "username": "alice"}]},
    )
    assert user_state.present("alice")["changes"] == {}


def test_user_absent(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(
        auth_c,
        "users_list",
        lambda o, profile=None: {"users": [{"id": "u-1", "username": "alice"}]},
    )
    monkeypatch.setattr(
        auth_c,
        "users_delete",
        lambda o, uid, profile=None: actions["deleted"].append(uid),
    )
    ret = user_state.absent("alice")
    assert ret["changes"] == {"deleted": "alice"}
    assert actions["deleted"] == ["u-1"]


def test_role_present(monkeypatch):
    actions = {"created": []}
    monkeypatch.setattr(auth_c, "roles_get_or_none", lambda o, n, profile=None: None)
    monkeypatch.setattr(
        auth_c,
        "roles_create",
        lambda o, spec, profile=None: actions["created"].append(spec),
    )
    ret = role_state.present("MyRole", privilege_keys=["READ"])
    assert ret["changes"] == {"new": "MyRole"}
    assert actions["created"][0]["privilege-keys"] == ["READ"]


def test_role_absent_refuses_system_role(monkeypatch):
    monkeypatch.setattr(
        auth_c,
        "roles_get_or_none",
        lambda o, n, profile=None: {"name": "Admin", "system-defined": True},
    )
    ret = role_state.absent("Admin")
    assert ret["changes"] == {}
    assert "system-defined" in ret["comment"]


def test_role_absent_deletes_custom(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(
        auth_c,
        "roles_get_or_none",
        lambda o, n, profile=None: {"name": "Custom", "system-defined": False},
    )
    monkeypatch.setattr(
        auth_c, "roles_delete", lambda o, n, profile=None: actions["deleted"].append(n)
    )
    ret = role_state.absent("Custom")
    assert ret["changes"] == {"deleted": "Custom"}


def test_supermetric_present_creates(monkeypatch):
    actions = {"created": [], "updated": []}
    monkeypatch.setattr(sm_c, "list_", lambda o: {"superMetrics": []})
    monkeypatch.setattr(sm_c, "create", lambda o, spec: actions["created"].append(spec))
    ret = sm_state.present("avg_cpu", formula="avg(${this})", description="x")
    assert ret["changes"] == {"new": "avg_cpu"}


def test_supermetric_present_matches_existing(monkeypatch):
    monkeypatch.setattr(
        sm_c,
        "list_",
        lambda o: {
            "superMetrics": [
                {
                    "id": "1",
                    "name": "avg_cpu",
                    "formula": "avg(${this})",
                    "description": "x",
                }
            ]
        },
    )
    ret = sm_state.present("avg_cpu", formula="avg(${this})", description="x")
    assert ret["changes"] == {}


def test_supermetric_present_updates_on_drift(monkeypatch):
    actions = {"updated": []}
    monkeypatch.setattr(
        sm_c,
        "list_",
        lambda o: {
            "superMetrics": [{"id": "1", "name": "avg_cpu", "formula": "old", "description": ""}]
        },
    )
    monkeypatch.setattr(sm_c, "update", lambda o, sid, spec: actions["updated"].append((sid, spec)))
    ret = sm_state.present("avg_cpu", formula="new")
    assert ret["changes"] == {"updated": "avg_cpu"}
    assert actions["updated"][0] == (
        "1",
        {"name": "avg_cpu", "formula": "new", "description": ""},
    )


def test_supermetric_absent(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(
        sm_c,
        "list_",
        lambda o: {"superMetrics": [{"id": "1", "name": "avg_cpu"}]},
    )
    monkeypatch.setattr(sm_c, "delete", lambda o, sid: actions["deleted"].append(sid))
    ret = sm_state.absent("avg_cpu")
    assert ret["changes"] == {"deleted": "avg_cpu"}
    assert actions["deleted"] == ["1"]
