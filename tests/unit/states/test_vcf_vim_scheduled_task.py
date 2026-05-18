"""Tests for the vim_scheduled_task state module."""

import pytest

from saltext.vcf.clients import vim_scheduled_task as c
from saltext.vcf.states import vcf_vim_scheduled_task as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_creates_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: None)
    monkeypatch.setattr(
        c,
        "create",
        lambda o, e, s, profile=None: calls.append((e, s)) or "st-99",
    )
    ret = st.present(
        "nightly-snapshot",
        entity="vm-1",
        spec={"name": "nightly-snapshot", "description": "x"},
    )
    assert ret["changes"] == {"created": "st-99"}
    assert calls[0][0] == "vm-1"


def test_present_idempotent_when_exists(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: {"id": "st-1"})
    monkeypatch.setattr(c, "create", lambda *a, **kw: pytest.fail("should not create"))
    ret = st.present("nightly", entity="vm-1", spec={"name": "nightly"})
    assert ret["changes"] == {}


def test_present_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: None)
    monkeypatch.setattr(c, "create", lambda *a, **kw: pytest.fail("should not create"))
    ret = st.present("nightly", entity="vm-1", spec={"name": "nightly"})
    assert ret["result"] is None


def test_absent_removes_when_present(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: {"id": "st-1"})
    monkeypatch.setattr(c, "delete", lambda o, n, profile=None: calls.append(n))
    ret = st.absent("nightly")
    assert ret["changes"] == {"removed": "st-1"}
    assert calls == ["nightly"]


def test_absent_idempotent(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: None)
    monkeypatch.setattr(c, "delete", lambda *a, **kw: pytest.fail("should not delete"))
    ret = st.absent("missing")
    assert ret["changes"] == {}
