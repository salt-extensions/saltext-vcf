"""Tests for states.vcf_nsx_identity_source."""

import pytest

from saltext.vcf.clients import nsx_identity_source as c
from saltext.vcf.states import vcf_nsx_identity_source as st


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
        lambda opts, body, profile=None: state["created"].append(body),
    )
    monkeypatch.setattr(
        c,
        "update",
        lambda opts, source_id, body, profile=None: state["updated"].append((source_id, body)),
    )
    monkeypatch.setattr(
        c,
        "delete",
        lambda opts, source_id, profile=None: state["deleted"].append(source_id),
    )
    return state


SPEC = {
    "type": "ActiveDirectoryOverLdap",
    "domain_name": "corp.example.com",
    "base_dn": "DC=corp,DC=example,DC=com",
    "ldap_servers": [{"url": "ldaps://ad1.corp:636"}],
    "bind_identity": "svc-nsx@corp",
    "user_search_filter": "(sAMAccountName=%s)",
}


def test_present_creates_when_missing(stub):
    ret = st.present("corp-ad", SPEC)
    assert ret["result"] is True
    assert ret["changes"] == {"new": "corp-ad"}
    assert stub["created"][0]["name"] == "corp-ad"
    assert stub["created"][0]["base_dn"] == SPEC["base_dn"]


def test_present_idempotent_when_matching(stub):
    stub["results"] = [{"id": "id-1", "name": "corp-ad", **SPEC}]
    ret = st.present("corp-ad", SPEC)
    assert ret["changes"] == {}
    assert ret["comment"].endswith("already matches")
    assert not stub["updated"]


def test_present_updates_when_field_differs(stub):
    current = {"id": "id-1", "name": "corp-ad", **SPEC}
    stub["results"] = [current]
    new_spec = dict(SPEC)
    new_spec["base_dn"] = "DC=corp2,DC=example,DC=com"
    ret = st.present("corp-ad", new_spec)
    assert "base_dn" in ret["changes"]
    assert stub["updated"]
    src_id, body = stub["updated"][0]
    assert src_id == "id-1"
    assert body["base_dn"] == "DC=corp2,DC=example,DC=com"


def test_present_password_always_updates(stub):
    """Password is opaque (not echoed back); when supplied it must be pushed."""
    stub["results"] = [{"id": "id-1", "name": "corp-ad", **SPEC}]
    spec_with_pw = dict(SPEC)
    spec_with_pw["password"] = "rotated"
    ret = st.present("corp-ad", spec_with_pw)
    assert "password" in ret["changes"]
    assert stub["updated"][0][1]["password"] == "rotated"


def test_present_no_password_stays_idempotent(stub):
    """When caller omits password, matching everything else is a no-op."""
    stub["results"] = [{"id": "id-1", "name": "corp-ad", **SPEC}]
    ret = st.present("corp-ad", SPEC)
    assert ret["changes"] == {}


def test_present_test_mode_would_create(stub, opts, monkeypatch):
    opts["test"] = True
    ret = st.present("corp-ad", SPEC)
    assert ret["result"] is None
    assert "would be created" in ret["comment"]
    assert not stub["created"]


def test_present_test_mode_would_update(stub, opts):
    opts["test"] = True
    stub["results"] = [{"id": "id-1", "name": "corp-ad", **SPEC}]
    new_spec = dict(SPEC)
    new_spec["base_dn"] = "DC=other,DC=example,DC=com"
    ret = st.present("corp-ad", new_spec)
    assert ret["result"] is None
    assert "would be updated" in ret["comment"]
    assert not stub["updated"]


def test_absent_when_missing(stub):
    ret = st.absent("corp-ad")
    assert ret["changes"] == {}
    assert "already absent" in ret["comment"]


def test_absent_deletes(stub):
    stub["results"] = [{"id": "id-1", "name": "corp-ad"}]
    ret = st.absent("corp-ad")
    assert ret["changes"] == {"deleted": "corp-ad"}
    assert stub["deleted"] == ["id-1"]


def test_absent_test_mode(stub, opts):
    opts["test"] = True
    stub["results"] = [{"id": "id-1", "name": "corp-ad"}]
    ret = st.absent("corp-ad")
    assert ret["result"] is None
    assert not stub["deleted"]
