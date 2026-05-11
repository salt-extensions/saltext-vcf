"""Tests for states.vmware_vcenter_cluster."""

import pytest
import requests

from saltext.vmware.clients import vcenter_cluster as r
from saltext.vmware.states import vmware_vcenter_cluster as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"created": [], "deleted": [], "exists": False, "raise_on_get": None}

    def fake_get_or_none(opts, name, profile=None):
        if state["raise_on_get"]:
            raise state["raise_on_get"]  # pylint: disable=raising-bad-type
        return {"name": name} if state["exists"] else None

    monkeypatch.setattr(r, "get_or_none", fake_get_or_none)
    monkeypatch.setattr(
        r,
        "create",
        lambda opts, name, profile=None, **k: state["created"].append((name, k)),
    )
    monkeypatch.setattr(r, "delete", lambda opts, name, profile=None: state["deleted"].append(name))
    return state


def test_present_already_present(stub):
    stub["exists"] = True
    ret = st.present("c1")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "already present" in ret["comment"]


def test_present_creates_when_missing(stub):
    ret = st.present("c1")
    assert ret["changes"] == {"new": "c1"}
    assert stub["created"][0][0] == "c1"


def test_present_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("c1")
    assert ret["result"] is None
    assert stub["created"] == []


def test_present_propagates_unexpected_error(stub):
    err = requests.HTTPError()
    err.response = type("R", (), {"status_code": 500})()
    stub["raise_on_get"] = err
    with pytest.raises(requests.HTTPError):
        st.present("c1")


def test_absent_already_absent(stub):
    ret = st.absent("c1")
    assert ret["changes"] == {}
    assert "already absent" in ret["comment"]


def test_absent_deletes(stub):
    stub["exists"] = True
    ret = st.absent("c1")
    assert ret["changes"] == {"deleted": "c1"}
    assert stub["deleted"] == ["c1"]
