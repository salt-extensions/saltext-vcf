"""Tests for states.vcf_vcenter_folder."""

import pytest

from saltext.vcf.clients import vcenter_folder as c
from saltext.vcf.states import vcf_vcenter_folder as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_already_exists(monkeypatch):
    monkeypatch.setattr(
        c, "find_by_name", lambda opts, name, profile=None: {"folder": "group-v1", "name": name}
    )
    ret = st.present("Edge Services", "VIRTUAL_MACHINE", datacenter="SDDC-Datacenter")
    assert ret["changes"] == {}


def test_present_creates(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "find_by_name", lambda opts, name, profile=None: None)
    monkeypatch.setattr(
        c,
        "create",
        lambda opts, name, folder_type, parent=None, datacenter=None, profile=None: calls.append(
            (name, folder_type, parent, datacenter)
        )
        or "group-v2",
    )
    ret = st.present("Edge Services", "VIRTUAL_MACHINE", datacenter="SDDC-Datacenter")
    assert ret["changes"] == {"new": "group-v2"}
    assert calls == [("Edge Services", "VIRTUAL_MACHINE", None, "SDDC-Datacenter")]


def test_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "find_by_name", lambda opts, name, profile=None: None)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("Edge Services", "VIRTUAL_MACHINE", datacenter="SDDC-Datacenter")
    assert ret["result"] is None


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "find_by_name", lambda opts, name, profile=None: None)
    ret = st.absent("Edge Services")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "find_by_name", lambda opts, name, profile=None: {"folder": "group-v1", "name": name}
    )
    monkeypatch.setattr(c, "delete", lambda opts, folder_id, profile=None: calls.append(folder_id))
    ret = st.absent("Edge Services")
    assert ret["changes"] == {"deleted": "Edge Services"}
    assert calls == ["group-v1"]


def test_absent_test_mode(monkeypatch):
    monkeypatch.setattr(
        c, "find_by_name", lambda opts, name, profile=None: {"folder": "group-v1", "name": name}
    )
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.absent("Edge Services")
    assert ret["result"] is None
