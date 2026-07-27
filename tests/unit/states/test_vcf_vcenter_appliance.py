"""Tests for states.vcf_vcenter_appliance."""

import pytest

from saltext.vcf.clients import vcenter_appliance as c
from saltext.vcf.states import vcf_vcenter_appliance as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "dns": {"mode": "is_static", "servers": []},
        "syslog": [],
        "ceip": {"accepted": True},
        "dns_set_calls": [],
        "syslog_set_calls": [],
        "ceip_set_calls": [],
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
    monkeypatch.setattr(c, "ceip_get", lambda opts, profile=None: state["ceip"])
    monkeypatch.setattr(
        c,
        "ceip_set",
        lambda opts, accepted, profile=None: state["ceip_set_calls"].append(bool(accepted)),
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


def test_ceip_set_no_change(stub):
    stub["ceip"] = {"accepted": False}
    ret = st.ceip_set("name", accepted=False)
    assert ret["changes"] == {}
    assert stub["ceip_set_calls"] == []
    assert ret["result"] is True


def test_ceip_set_disables_when_accepted(stub):
    stub["ceip"] = {"accepted": True}
    ret = st.ceip_set("name", accepted=False)
    assert ret["changes"] == {"accepted": {"old": True, "new": False}}
    assert stub["ceip_set_calls"] == [False]


def test_ceip_set_enables_when_declined(stub):
    stub["ceip"] = {"accepted": False}
    ret = st.ceip_set("name", accepted=True)
    assert ret["changes"] == {"accepted": {"old": False, "new": True}}
    assert stub["ceip_set_calls"] == [True]


def test_ceip_set_tolerates_value_wrapper(stub):
    """Some vCenter builds wrap the response as ``{"value": {"accepted": ...}}``."""
    stub["ceip"] = {"value": {"accepted": True}}
    ret = st.ceip_set("name", accepted=False)
    assert ret["changes"] == {"accepted": {"old": True, "new": False}}
    assert stub["ceip_set_calls"] == [False]


def test_ceip_set_test_mode(monkeypatch, stub):
    stub["ceip"] = {"accepted": True}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.ceip_set("name", accepted=False)
    assert ret["result"] is None
    assert stub["ceip_set_calls"] == []
    assert "would change" in ret["comment"]


def test_ceip_disabled_shortcut(stub):
    stub["ceip"] = {"accepted": True}
    ret = st.ceip_disabled("name")
    assert stub["ceip_set_calls"] == [False]
    assert ret["changes"] == {"accepted": {"old": True, "new": False}}
