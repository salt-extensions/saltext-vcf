"""Tests for states.vcf_vcenter_localos_user."""

import pytest

from saltext.vcf.clients import vcenter_localos_user as c
from saltext.vcf.states import vcf_vcenter_localos_user as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_creates_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: None)
    monkeypatch.setattr(
        c,
        "create",
        lambda opts, name, password, roles, profile=None, **extra: calls.append(
            (name, password, roles, extra)
        ),
    )
    ret = st.present("bob", "s3cret", ["operator"], email="bob@example.test")
    assert ret["changes"] == {"new": "bob"}
    assert calls == [("bob", "s3cret", ["operator"], {"enabled": True, "email": "bob@example.test"})]


def test_present_test_mode_when_missing(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: None)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("bob", "s3cret", ["operator"])
    assert ret["result"] is None


def test_present_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda opts, name, profile=None: {"roles": ["operator"], "enabled": True, "email": None},
    )
    ret = st.present("bob", "s3cret", ["operator"], enabled=True)
    assert ret["changes"] == {}


def test_present_updates_diff(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda opts, name, profile=None: {"roles": ["operator"], "enabled": True},
    )
    monkeypatch.setattr(
        c, "update", lambda opts, name, profile=None, **diff: calls.append((name, diff))
    )
    ret = st.present("bob", "s3cret", ["admin"], enabled=True)
    assert ret["changes"] == {"roles": ["admin"]}
    assert calls == [("bob", {"roles": ["admin"]})]


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: None)
    ret = st.absent("bob")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: {"username": "bob"})
    monkeypatch.setattr(c, "delete", lambda opts, name, profile=None: calls.append(name))
    ret = st.absent("bob")
    assert ret["changes"] == {"deleted": "bob"}
    assert calls == ["bob"]
