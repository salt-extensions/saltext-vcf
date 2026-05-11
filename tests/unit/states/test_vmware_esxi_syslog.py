"""Tests for states.vmware_esxi_syslog."""

import pytest

from saltext.vmware.clients import esxi_syslog as c
from saltext.vmware.states import vmware_esxi_syslog as st


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
        "set_log_level",
        lambda opts, level, profile=None: state["calls"].append(("level", level)),
    )
    return state


def test_already_matches(stub):
    stub["current"] = {"servers": ["udp://a:514"], "log_level": "INFO"}
    ret = st.servers("syslog", ["udp://a:514"], log_level="INFO")
    assert ret["changes"] == {}


def test_change_servers_and_level(stub):
    stub["current"] = {"servers": [], "log_level": "INFO"}
    ret = st.servers("syslog", ["udp://collector:514"], log_level="DEBUG")
    assert ret["changes"]["servers"]["new"] == ["udp://collector:514"]
    assert ret["changes"]["log_level"]["new"] == "DEBUG"
    assert ("servers", ["udp://collector:514"]) in stub["calls"]
    assert ("level", "DEBUG") in stub["calls"]
