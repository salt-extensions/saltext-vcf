"""Tests for the vcf_vim_vm_snapshot state module."""

import pytest

from saltext.vcf.clients import vim_vm_snapshot as c
from saltext.vcf.states import vcf_vim_vm_snapshot as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_noop_when_exists(monkeypatch):
    monkeypatch.setattr(c, "state", lambda o, v, s, profile=None: {"present": True})
    ret = st.present("vm-100", "pre-patch")
    assert ret["changes"] == {}
    assert "already present" in ret["comment"]


def test_present_creates(monkeypatch):
    monkeypatch.setattr(c, "state", lambda o, v, s, profile=None: {"present": False})
    captured = {}

    def _create(o, v, name, **kw):
        captured.update(kw)
        captured["name"] = name

    monkeypatch.setattr(c, "create", _create)
    ret = st.present("vm-100", "pre-patch", description="d", include_memory=True, quiesce=True)
    assert ret["changes"] == {"new": "pre-patch"}
    assert captured == {
        "name": "pre-patch",
        "description": "d",
        "memory": True,
        "quiesce": True,
        "profile": None,
    }


def test_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "state", lambda o, v, s, profile=None: {"present": False})
    monkeypatch.setattr(
        c, "create", lambda *a, **kw: pytest.fail("must not create in test mode")
    )
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("vm-100", "pre-patch")
    assert ret["result"] is None
    assert ret["changes"] == {"new": "pre-patch"}


def test_absent_noop_when_missing(monkeypatch):
    monkeypatch.setattr(c, "state", lambda o, v, s, profile=None: {"present": False})
    ret = st.absent("vm-100", "pre-patch")
    assert ret["changes"] == {}


def test_absent_removes(monkeypatch):
    monkeypatch.setattr(c, "state", lambda o, v, s, profile=None: {"present": True})
    called = {}
    monkeypatch.setattr(c, "remove", lambda o, v, s, **kw: called.update(s=s, **kw))
    ret = st.absent("vm-100", "pre-patch", remove_children=True)
    assert ret["changes"] == {"old": "pre-patch"}
    assert called["remove_children"] is True
