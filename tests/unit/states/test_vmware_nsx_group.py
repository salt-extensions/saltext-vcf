"""Tests for states.vmware_nsx_group."""

import pytest

from saltext.vmware.clients import nsx_group as r
from saltext.vmware.states import vmware_nsx_group as st


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
    assert st.present("g-a")["changes"] == {}


def test_present_creates(stub):
    ret = st.present("g-a", expression=[{"resource_type": "Condition"}])
    assert ret["changes"] == {"new": "g-a"}
    assert stub["created"][0][0] == "g-a"


def test_absent_already(stub):
    assert st.absent("g-a")["changes"] == {}


def test_absent_deletes(stub):
    stub["exists"] = True
    ret = st.absent("g-a")
    assert ret["changes"] == {"deleted": "g-a"}
