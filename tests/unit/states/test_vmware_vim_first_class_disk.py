"""Tests for the FCD state module."""

import pytest

from saltext.vmware.clients import vim_first_class_disk as c
from saltext.vmware.states import vmware_vim_first_class_disk as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _fcd(name="disk", capacity_gb=10, keep=False):
    return {
        "id": "vslm-1",
        "name": name,
        "capacity_bytes": int(capacity_gb) * 1024 * 1024 * 1024,
        "keep_after_delete_vm": keep,
    }


def test_present_creates_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [])
    monkeypatch.setattr(
        c,
        "create",
        lambda o, n, d, capacity_gb, **kw: calls.append((n, d, capacity_gb)) or "task-c",
    )
    ret = st.present("disk", datastore="ds-1", capacity_gb=10)
    assert ret["changes"]["created_task"] == "task-c"
    assert calls[0] == ("disk", "ds-1", 10)


def test_present_idempotent(monkeypatch):
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [_fcd(capacity_gb=10)])
    monkeypatch.setattr(c, "create", lambda *a, **kw: pytest.fail("no create"))
    monkeypatch.setattr(c, "extend", lambda *a, **kw: pytest.fail("no extend"))
    ret = st.present("disk", datastore="ds-1", capacity_gb=10)
    assert ret["changes"] == {}


def test_present_extends_when_smaller(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [_fcd(capacity_gb=10)])
    monkeypatch.setattr(
        c, "extend", lambda o, vid, d, new, profile=None: calls.append(new) or "task-grow"
    )
    monkeypatch.setattr(c, "set_keep_after_delete_vm", lambda *a, **kw: True)
    ret = st.present("disk", datastore="ds-1", capacity_gb=20)
    assert "capacity_bytes" in ret["changes"]
    assert calls == [20]


def test_present_does_not_shrink(monkeypatch):
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [_fcd(capacity_gb=50)])
    monkeypatch.setattr(c, "extend", lambda *a, **kw: pytest.fail("no shrink"))
    ret = st.present("disk", datastore="ds-1", capacity_gb=20)
    assert ret["changes"] == {}


def test_present_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [])
    monkeypatch.setattr(c, "create", lambda *a, **kw: pytest.fail("no create"))
    ret = st.present("disk", datastore="ds-1", capacity_gb=10)
    assert ret["result"] is None


def test_absent_when_missing(monkeypatch):
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [])
    ret = st.absent("disk", datastore="ds-1")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "list_", lambda o, d, profile=None: [_fcd()])
    monkeypatch.setattr(c, "delete", lambda o, vid, d, profile=None: calls.append(vid))
    ret = st.absent("disk", datastore="ds-1")
    assert ret["changes"]["deleted"] == "vslm-1"
    assert calls == ["vslm-1"]
