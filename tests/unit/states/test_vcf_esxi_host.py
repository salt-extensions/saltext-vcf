"""Tests for states.vcf_esxi_host."""

import pytest

from saltext.vcf.clients import esxi_host as c
from saltext.vcf.states import vcf_esxi_host as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "info": {"in_maintenance_mode": False},
        "calls": [],
        "lockdown": {"mode": "DISABLED"},
    }

    monkeypatch.setattr(c, "info", lambda opts, profile=None: state["info"])
    monkeypatch.setattr(c, "lockdown_get", lambda opts, profile=None: state["lockdown"])
    monkeypatch.setattr(
        c,
        "lockdown_set",
        lambda opts, mode, exception_users=None, profile=None: state["calls"].append(
            ("lockdown_set", mode, exception_users)
        ),
    )
    monkeypatch.setattr(
        c,
        "enter_maintenance",
        lambda opts, profile=None: state["calls"].append(("enter",)),
    )
    monkeypatch.setattr(
        c,
        "exit_maintenance",
        lambda opts, profile=None: state["calls"].append(("exit",)),
    )
    return state


def test_maintenance_noop(stub):
    stub["info"] = {"in_maintenance_mode": True}
    ret = st.maintenance("esxi01", enabled=True)
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_maintenance_enter(stub):
    stub["info"] = {"in_maintenance_mode": False}
    ret = st.maintenance("esxi01", enabled=True)
    assert ret["changes"] == {"maintenance": True}
    assert stub["calls"] == [("enter",)]


def test_maintenance_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["info"] = {"in_maintenance_mode": False}
    ret = st.maintenance("esxi01", enabled=True)
    assert ret["result"] is None
    assert stub["calls"] == []


def test_lockdown_change(stub):
    stub["lockdown"] = {"mode": "DISABLED", "exception_users": []}
    ret = st.lockdown("esxi01", mode="NORMAL", exception_users=["root"])
    assert ret["changes"]["mode"] == {"old": "DISABLED", "new": "NORMAL"}
    assert ret["changes"]["exception_users"]["new"] == ["root"]
    assert stub["calls"] == [("lockdown_set", "NORMAL", ["root"])]


def test_lockdown_noop(stub):
    stub["lockdown"] = {"mode": "NORMAL", "exception_users": ["root"]}
    ret = st.lockdown("esxi01", mode="NORMAL", exception_users=["root"])
    assert ret["changes"] == {}
