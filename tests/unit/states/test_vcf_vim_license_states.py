"""Tests for the vcf_vim_license state module."""

import pytest

from saltext.vcf.clients import vim_license as c
from saltext.vcf.states import vcf_vim_license as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_adds_and_assigns(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, k, profile=None: None)
    monkeypatch.setattr(c, "assigned_list", lambda o, profile=None: [])
    monkeypatch.setattr(c, "add", lambda o, k, profile=None: None)
    monkeypatch.setattr(c, "resolve_entity", lambda o, **kw: "domain-c9")
    assigned = []
    monkeypatch.setattr(c, "assign_by_name", lambda o, k, **kw: assigned.append(k))
    ret = st.present("ABCDE-12345")
    assert ret["changes"]["new"] == "ABCDE-12345"
    assert ret["changes"]["assigned_to"] == "domain-c9"
    assert assigned == ["ABCDE-12345"]


def test_present_already_assigned(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda o, k, profile=None: {"license_key": k, "name": "lic"},
    )
    monkeypatch.setattr(
        c,
        "assigned_list",
        lambda o, profile=None: [
            {"entity_id": "domain-c9", "assigned_license": {"license_key": "ABCDE-12345"}}
        ],
    )
    monkeypatch.setattr(c, "resolve_entity", lambda o, **kw: "domain-c9")
    ret = st.present("ABCDE-12345")
    assert ret["changes"] == {}
    assert "already" in ret["comment"]


def test_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, k, profile=None: None)
    monkeypatch.setattr(c, "add", lambda *a, **kw: pytest.fail("must not add"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("ABCDE-12345")
    assert ret["result"] is None
    assert ret["changes"] == {"new": "ABCDE-12345"}


def test_absent_removes(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, k, profile=None: {"license_key": k})
    monkeypatch.setattr(c, "remove", lambda o, k, profile=None: True)
    ret = st.absent("ABCDE-12345")
    assert ret["changes"] == {"old": "ABCDE-12345"}


def test_absent_noop(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, k, profile=None: None)
    ret = st.absent("ABCDE-12345")
    assert ret["changes"] == {}
