"""Tests for states.vcf_vrli_settings."""

import pytest

from saltext.vcf.clients import vrli_settings as c
from saltext.vcf.states import vcf_vrli_settings as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub_timeout(monkeypatch):
    state = {"current": 900, "calls": []}
    monkeypatch.setattr(c, "get_session_timeout", lambda o, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "set_session_timeout",
        lambda o, seconds, profile=None: state["calls"].append(seconds),
    )
    return state


def test_session_timeout_change(stub_timeout):
    ret = st.session_timeout_configured("t", seconds=1800)
    assert ret["changes"] == {"session_timeout_seconds": {"old": 900, "new": 1800}}
    assert stub_timeout["calls"] == [1800]


def test_session_timeout_idempotent(stub_timeout):
    stub_timeout["current"] = 1800
    ret = st.session_timeout_configured("t", seconds=1800)
    assert ret["changes"] == {}
    assert stub_timeout["calls"] == []


def test_session_timeout_test_mode(stub_timeout, opts):
    opts["test"] = True
    ret = st.session_timeout_configured("t", seconds=1800)
    assert ret["result"] is None
    assert stub_timeout["calls"] == []


@pytest.fixture
def stub_dns(monkeypatch):
    state = {"current": ["10.0.0.53"], "calls": []}
    monkeypatch.setattr(
        c, "get_dns_servers_from_appliance", lambda o, profile=None: state["current"]
    )
    monkeypatch.setattr(
        c,
        "set_dns_servers",
        lambda o, servers, profile=None: state["calls"].append(list(servers)),
    )
    return state


def test_dns_servers_idempotent_regardless_of_order(stub_dns):
    stub_dns["current"] = ["10.0.0.53", "10.0.0.54"]
    ret = st.dns_servers_configured("d", ["10.0.0.54", "10.0.0.53"])
    assert ret["changes"] == {}
    assert stub_dns["calls"] == []


def test_dns_servers_writes_when_different(stub_dns):
    ret = st.dns_servers_configured("d", ["10.0.0.53", "10.0.0.54"])
    assert stub_dns["calls"] == [["10.0.0.53", "10.0.0.54"]]
    assert ret["changes"]["dns_servers"]["new"] == ["10.0.0.53", "10.0.0.54"]


def test_dns_servers_test_mode(stub_dns, opts):
    opts["test"] = True
    ret = st.dns_servers_configured("d", ["10.0.0.99"])
    assert ret["result"] is None
    assert stub_dns["calls"] == []
