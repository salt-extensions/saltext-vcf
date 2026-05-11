"""Tests for states.vmware_nsx_segment."""

import pytest

from saltext.vmware.clients import nsx_segment as r
from saltext.vmware.states import vmware_nsx_segment as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"exists": False, "created": [], "deleted": []}

    monkeypatch.setattr(
        r,
        "get_or_none",
        lambda opts, name, profile=None: {"id": name} if state["exists"] else None,
    )
    monkeypatch.setattr(
        r,
        "create",
        lambda opts, name, profile=None, **k: state["created"].append((name, k)),
    )
    monkeypatch.setattr(r, "delete", lambda opts, name, profile=None: state["deleted"].append(name))
    return state


def test_present_already(stub):
    stub["exists"] = True
    assert st.present("seg-a")["changes"] == {}


def test_present_creates(stub):
    ret = st.present("seg-a", transport_zone_path="/tz/1")
    assert ret["changes"] == {"new": "seg-a"}
    assert stub["created"][0][0] == "seg-a"
    assert stub["created"][0][1]["transport_zone_path"] == "/tz/1"


def test_absent_when_already_gone(stub):
    ret = st.absent("seg-a")
    assert ret["changes"] == {}


def test_absent_deletes(stub):
    stub["exists"] = True
    ret = st.absent("seg-a")
    assert ret["changes"] == {"deleted": "seg-a"}
    assert stub["deleted"] == ["seg-a"]


def test_present_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("seg-a")
    assert ret["result"] is None
