"""Tests for states.vmware_nsx_role_binding."""

import pytest

from saltext.vmware.clients import nsx_role_binding as c
from saltext.vmware.states import vmware_nsx_role_binding as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"results": [], "created": [], "updated": [], "deleted": []}

    monkeypatch.setattr(c, "list_", lambda opts, profile=None: {"results": state["results"]})
    monkeypatch.setattr(
        c,
        "create",
        lambda opts, name, type_, roles, profile=None, **k: state["created"].append(
            (name, type_, roles)
        ),
    )
    monkeypatch.setattr(
        c,
        "update",
        lambda opts, binding_id, body, profile=None: state["updated"].append((binding_id, body)),
    )
    monkeypatch.setattr(
        c,
        "delete",
        lambda opts, binding_id, profile=None: state["deleted"].append(binding_id),
    )
    return state


def test_present_creates_when_missing(stub):
    ret = st.present("alice", "remote_user", [{"role": "auditor"}])
    assert ret["changes"] == {"new": "alice"}
    assert stub["created"][0][0] == "alice"


def test_present_idempotent(stub):
    stub["results"] = [
        {
            "id": "rb-1",
            "name": "alice",
            "type": "remote_user",
            "roles": [{"role": "auditor"}],
        }
    ]
    ret = st.present("alice", "remote_user", [{"role": "auditor"}])
    assert ret["changes"] == {}


def test_present_updates_role_diff(stub):
    stub["results"] = [
        {
            "id": "rb-1",
            "name": "alice",
            "type": "remote_user",
            "roles": [{"role": "auditor"}],
        }
    ]
    ret = st.present("alice", "remote_user", [{"role": "enterprise_admin"}])
    assert "roles" in ret["changes"]
    assert stub["updated"]
    assert stub["updated"][0][0] == "rb-1"


def test_absent_when_missing(stub):
    ret = st.absent("alice")
    assert ret["changes"] == {}


def test_absent_deletes(stub):
    stub["results"] = [{"id": "rb-1", "name": "alice", "type": "remote_user", "roles": []}]
    ret = st.absent("alice")
    assert ret["changes"] == {"deleted": "alice"}
    assert stub["deleted"] == ["rb-1"]
