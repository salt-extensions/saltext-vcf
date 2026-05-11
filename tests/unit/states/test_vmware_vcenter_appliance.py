"""Tests for states.vmware_vcenter_appliance."""

import pytest

from saltext.vmware.clients import vcenter_appliance as c
from saltext.vmware.states import vmware_vcenter_appliance as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "dns": {"mode": "is_static", "servers": []},
        "syslog": [],
        "dns_set_calls": [],
        "syslog_set_calls": [],
    }

    monkeypatch.setattr(c, "dns_get", lambda opts, profile=None: state["dns"])
    monkeypatch.setattr(
        c,
        "dns_set",
        lambda opts, servers, mode="is_static", profile=None: state["dns_set_calls"].append(
            (list(servers), mode)
        ),
    )
    monkeypatch.setattr(c, "logging_forwarding_get", lambda opts, profile=None: state["syslog"])
    monkeypatch.setattr(
        c,
        "logging_forwarding_set",
        lambda opts, servers, profile=None: state["syslog_set_calls"].append(list(servers)),
    )
    return state


def test_dns_no_change(stub):
    stub["dns"] = {"mode": "is_static", "servers": ["1.1.1.1", "8.8.8.8"]}
    ret = st.dns_servers("name", ["8.8.8.8", "1.1.1.1"], mode="is_static")
    assert ret["changes"] == {}
    assert stub["dns_set_calls"] == []


def test_dns_changes_servers(stub):
    stub["dns"] = {"mode": "is_static", "servers": ["1.1.1.1"]}
    ret = st.dns_servers("name", ["8.8.8.8"], mode="is_static")
    assert "servers" in ret["changes"]
    assert stub["dns_set_calls"] == [(["8.8.8.8"], "is_static")]


def test_dns_changes_mode(stub):
    stub["dns"] = {"mode": "dhcp", "servers": []}
    ret = st.dns_servers("name", [], mode="is_static")
    assert ret["changes"]["mode"]["new"] == "is_static"


def test_dns_test_mode(monkeypatch, stub):
    stub["dns"] = {"mode": "is_static", "servers": []}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.dns_servers("name", ["a"])
    assert ret["result"] is None
    assert stub["dns_set_calls"] == []


def test_logging_forwarding_no_change(stub):
    fwd = [{"hostname": "c", "port": 514, "protocol": "UDP"}]
    stub["syslog"] = fwd
    ret = st.logging_forwarding("name", fwd)
    assert ret["changes"] == {}


def test_logging_forwarding_change(stub):
    stub["syslog"] = []
    new = [{"hostname": "c", "port": 514, "protocol": "UDP"}]
    ret = st.logging_forwarding("name", new)
    assert ret["changes"]["forwarders"]["new"] == new
    assert stub["syslog_set_calls"] == [new]
