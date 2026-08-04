"""Tests for states.vcf_vcenter_content_library."""

import pytest

from saltext.vcf.clients import vcenter_content_library as c
from saltext.vcf.states import vcf_vcenter_content_library as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


STORAGE_BACKINGS = [{"type": "DATASTORE", "datastore_id": "datastore-1"}]


def test_present_already_exists(monkeypatch):
    monkeypatch.setattr(
        c, "find_libraries", lambda opts, name=None, type=None, profile=None: ["lib-1"]
    )
    monkeypatch.setattr(
        c, "get_or_none", lambda opts, library_id, profile=None: {"id": library_id, "name": "Isos"}
    )
    ret = st.present("Isos", STORAGE_BACKINGS)
    assert ret["changes"] == {}


def test_present_creates(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "find_libraries", lambda opts, name=None, type=None, profile=None: [])
    monkeypatch.setattr(
        c,
        "create_local",
        lambda opts, name, storage_backings, profile=None, **spec: calls.append(
            (name, storage_backings, spec)
        )
        or "lib-2",
    )
    ret = st.present("Isos", STORAGE_BACKINGS, description="OS isos")
    assert ret["changes"] == {"new": "lib-2"}
    assert calls == [("Isos", STORAGE_BACKINGS, {"description": "OS isos"})]


def test_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "find_libraries", lambda opts, name=None, type=None, profile=None: [])
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("Isos", STORAGE_BACKINGS)
    assert ret["result"] is None


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "find_libraries", lambda opts, name=None, type=None, profile=None: [])
    ret = st.absent("Isos")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "find_libraries", lambda opts, name=None, type=None, profile=None: ["lib-1"]
    )
    monkeypatch.setattr(
        c, "get_or_none", lambda opts, library_id, profile=None: {"id": library_id, "name": "Isos"}
    )
    monkeypatch.setattr(
        c, "delete_local", lambda opts, library_id, profile=None: calls.append(library_id)
    )
    ret = st.absent("Isos")
    assert ret["changes"] == {"deleted": "Isos"}
    assert calls == ["lib-1"]


def test_absent_test_mode(monkeypatch):
    monkeypatch.setattr(
        c, "find_libraries", lambda opts, name=None, type=None, profile=None: ["lib-1"]
    )
    monkeypatch.setattr(
        c, "get_or_none", lambda opts, library_id, profile=None: {"id": library_id, "name": "Isos"}
    )
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.absent("Isos")
    assert ret["result"] is None
