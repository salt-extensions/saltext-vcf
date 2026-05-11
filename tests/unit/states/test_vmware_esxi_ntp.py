"""Tests for states.vmware_esxi_ntp."""

import pytest

from saltext.vmware.clients import esxi_ntp as c
from saltext.vmware.states import vmware_esxi_ntp as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": {}, "calls": []}

    monkeypatch.setattr(c, "get", lambda opts, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "set_servers",
        lambda opts, servers, profile=None: state["calls"].append(("servers", list(servers))),
    )
    monkeypatch.setattr(
        c,
        "set_enabled",
        lambda opts, enabled, profile=None: state["calls"].append(("enabled", enabled)),
    )
    return state


def test_already_matches(stub):
    stub["current"] = {"servers": ["a", "b"], "enabled": True}
    ret = st.servers("ntp", ["b", "a"], enabled=True)
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_change_servers(stub):
    stub["current"] = {"servers": ["old"], "enabled": True}
    ret = st.servers("ntp", ["a", "b"], enabled=True)
    assert ret["changes"]["servers"]["new"] == ["a", "b"]
    assert ("servers", ["a", "b"]) in stub["calls"]


def test_change_enabled(stub):
    stub["current"] = {"servers": ["a"], "enabled": False}
    ret = st.servers("ntp", ["a"], enabled=True)
    assert ret["changes"]["enabled"] == {"old": False, "new": True}
    assert ("enabled", True) in stub["calls"]


def test_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["current"] = {"servers": [], "enabled": False}
    ret = st.servers("ntp", ["a"], enabled=True)
    assert ret["result"] is None
    assert stub["calls"] == []
