"""Tests for states.vcf_vcenter_host."""

import pytest

from saltext.vcf.clients import vcenter_host as r
from saltext.vcf.states import vcf_vcenter_host as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": None, "calls": []}

    monkeypatch.setattr(r, "get_or_none", lambda opts, name, profile=None: state["current"])
    monkeypatch.setattr(
        r,
        "enter_maintenance",
        lambda opts, name, profile=None: state["calls"].append(("enter", name)),
    )
    monkeypatch.setattr(
        r,
        "exit_maintenance",
        lambda opts, name, profile=None: state["calls"].append(("exit", name)),
    )
    return state


def test_present_when_visible(stub):
    stub["current"] = {"name": "h1", "connection_state": "CONNECTED"}
    ret = st.present("h1")
    assert ret["result"] is True
    assert "present" in ret["comment"]


def test_present_reports_failure_when_missing(stub):
    ret = st.present("h1")
    assert ret["result"] is False
    assert "commission" in ret["comment"]


def test_absent_when_missing(stub):
    ret = st.absent("h1")
    assert ret["result"] is True


def test_maintenance_enter(stub):
    stub["current"] = {"connection_state": "CONNECTED"}
    ret = st.maintenance("h1", enabled=True)
    assert ret["changes"] == {"maintenance": True}
    assert stub["calls"] == [("enter", "h1")]


def test_maintenance_exit(stub):
    stub["current"] = {"connection_state": "MAINTENANCE"}
    ret = st.maintenance("h1", enabled=False)
    assert ret["changes"] == {"maintenance": False}
    assert stub["calls"] == [("exit", "h1")]


def test_maintenance_noop(stub):
    stub["current"] = {"connection_state": "MAINTENANCE"}
    ret = st.maintenance("h1", enabled=True)
    assert ret["changes"] == {}


def test_maintenance_test_mode(monkeypatch, stub):
    stub["current"] = {"connection_state": "CONNECTED"}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.maintenance("h1", enabled=True)
    assert ret["result"] is None
    assert stub["calls"] == []
