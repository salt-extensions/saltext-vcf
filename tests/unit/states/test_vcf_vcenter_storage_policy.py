"""Tests for states.vcf_vcenter_storage_policy."""

import pytest

from saltext.vcf.clients import vcenter_storage_policy as c
from saltext.vcf.states import vcf_vcenter_storage_policy as st

CONSTRAINTS = [{"tags": {"cat1": ["gold"]}}]


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_creates_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_by_name", lambda opts, name, profile=None: None)
    monkeypatch.setattr(
        c,
        "create",
        lambda opts, name, constraints, description=None, profile=None: calls.append(
            (name, constraints, description)
        )
        or "id-1",
    )
    ret = st.present("my-policy", CONSTRAINTS, description="desc")
    assert ret["changes"] == {"new": "id-1"}
    assert calls == [("my-policy", CONSTRAINTS, "desc")]


def test_present_test_mode_when_missing(monkeypatch):
    monkeypatch.setattr(c, "get_by_name", lambda opts, name, profile=None: None)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("my-policy", CONSTRAINTS)
    assert ret["result"] is None


def test_present_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_by_name",
        lambda opts, name, profile=None: {
            "id": "id-1",
            "description": "desc",
            "constraints": CONSTRAINTS,
        },
    )
    ret = st.present("my-policy", CONSTRAINTS, description="desc")
    assert ret["changes"] == {}


def test_present_updates_on_constraint_diff(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "get_by_name",
        lambda opts, name, profile=None: {
            "id": "id-1",
            "description": "desc",
            "constraints": [{"tags": {"cat1": ["silver"]}}],
        },
    )
    monkeypatch.setattr(
        c,
        "update",
        lambda opts, name, constraints=None, description=None, profile=None: calls.append(
            (name, constraints, description)
        ),
    )
    ret = st.present("my-policy", CONSTRAINTS, description="desc")
    assert "constraints" in ret["changes"]
    assert calls == [("my-policy", CONSTRAINTS, "desc")]


def test_default_policy_unknown_policy(monkeypatch):
    monkeypatch.setattr(c, "get_by_name", lambda opts, name, profile=None: None)
    ret = st.default_policy("vsan-default", "vsanDatastore", "nope")
    assert ret["result"] is False


def test_default_policy_already_set(monkeypatch):
    monkeypatch.setattr(
        c, "get_by_name", lambda opts, name, profile=None: {"id": "id-1", "name": name}
    )
    monkeypatch.setattr(c, "default_policy_get", lambda opts, datastore, profile=None: "id-1")
    ret = st.default_policy("vsan-default", "vsanDatastore", "raid0-vm-policy")
    assert ret["changes"] == {}


def test_default_policy_changes(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "get_by_name", lambda opts, name, profile=None: {"id": "id-2", "name": name}
    )
    monkeypatch.setattr(c, "default_policy_get", lambda opts, datastore, profile=None: "id-1")
    monkeypatch.setattr(
        c,
        "default_policy_set",
        lambda opts, datastore, policy, profile=None: calls.append((datastore, policy)),
    )
    ret = st.default_policy("vsan-default", "vsanDatastore", "raid0-vm-policy")
    assert ret["changes"] == {"default_policy": {"old": "id-1", "new": "id-2"}}
    assert calls == [("vsanDatastore", "raid0-vm-policy")]


def test_default_policy_test_mode(monkeypatch):
    monkeypatch.setattr(
        c, "get_by_name", lambda opts, name, profile=None: {"id": "id-2", "name": name}
    )
    monkeypatch.setattr(c, "default_policy_get", lambda opts, datastore, profile=None: "id-1")
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.default_policy("vsan-default", "vsanDatastore", "raid0-vm-policy")
    assert ret["result"] is None


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "get_by_name", lambda opts, name, profile=None: None)
    ret = st.absent("my-policy")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "get_by_name", lambda opts, name, profile=None: {"id": "id-1", "name": name}
    )
    monkeypatch.setattr(c, "delete", lambda opts, name, profile=None: calls.append(name))
    ret = st.absent("my-policy")
    assert ret["changes"] == {"deleted": "my-policy"}
    assert calls == ["my-policy"]
