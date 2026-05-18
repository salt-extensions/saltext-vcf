"""Tests for states.vcf_vim_extension."""

import pytest

from saltext.vcf.clients import vim_extension as c
from saltext.vcf.states import vcf_vim_extension as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": None, "registered": [], "updated": [], "unregistered": []}

    monkeypatch.setattr(c, "get_or_none", lambda opts, key, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "register",
        lambda opts, key, version, description, company, profile=None, **f: state[
            "registered"
        ].append((key, version, description, company, f)),
    )
    monkeypatch.setattr(
        c,
        "update",
        lambda opts, key, version=None, description=None, profile=None, **f: state[
            "updated"
        ].append((key, version, description, f)),
    )
    monkeypatch.setattr(
        c,
        "unregister",
        lambda opts, key, profile=None: state["unregistered"].append(key),
    )
    return state


def test_registered_creates(stub):
    ret = st.registered("com.example.salt", "1.0", "Salt", "Example")
    assert ret["changes"] == {"new": "com.example.salt"}
    assert stub["registered"][0][0] == "com.example.salt"


def test_registered_idempotent(stub):
    stub["current"] = {
        "key": "com.example.salt",
        "version": "1.0",
        "description": "Salt",
        "company": "Example",
    }
    ret = st.registered("com.example.salt", "1.0", "Salt", "Example")
    assert ret["changes"] == {}
    assert stub["registered"] == []


def test_registered_updates_on_version_drift(stub):
    stub["current"] = {
        "key": "com.example.salt",
        "version": "1.0",
        "description": "Salt",
        "company": "Example",
    }
    ret = st.registered("com.example.salt", "2.0", "Salt", "Example")
    assert ret["changes"]["version"]["new"] == "2.0"
    assert stub["updated"][0][0] == "com.example.salt"


def test_unregistered_removes_existing(stub):
    stub["current"] = {"key": "com.example.salt"}
    ret = st.unregistered("com.example.salt")
    assert ret["changes"] == {"deleted": "com.example.salt"}
    assert stub["unregistered"] == ["com.example.salt"]


def test_unregistered_idempotent(stub):
    ret = st.unregistered("com.example.salt")
    assert ret["changes"] == {}
    assert stub["unregistered"] == []


def test_registered_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.registered("com.example.salt", "1.0", "Salt", "Example")
    assert ret["result"] is None
    assert stub["registered"] == []
