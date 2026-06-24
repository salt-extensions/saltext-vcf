"""Tests for VMSP states (ntp/dns/syslog)."""

import pytest

from saltext.vcf.clients import vmsp_dns as dns_client
from saltext.vcf.clients import vmsp_ntp as ntp_client
from saltext.vcf.clients import vmsp_syslog as syslog_client
from saltext.vcf.states import vcf_vmsp_dns as dns_state
from saltext.vcf.states import vcf_vmsp_ntp as ntp_state
from saltext.vcf.states import vcf_vmsp_syslog as syslog_state


@pytest.fixture
def ntp_stub(monkeypatch):
    state = {"current": ["1.1.1.1"], "applied": []}
    monkeypatch.setattr(ntp_client, "get", lambda opts, profile=None: {"servers": state["current"]})
    monkeypatch.setattr(
        ntp_client, "set_", lambda opts, servers, profile=None: state["applied"].append(servers)
    )
    return state


def test_ntp_already_compliant(monkeypatch, ntp_stub):
    monkeypatch.setattr(ntp_state, "__opts__", {"test": False}, raising=False)
    ret = ntp_state.compliant("ntp", servers=["1.1.1.1"])
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert ntp_stub["applied"] == []


def test_ntp_test_mode_reports_drift(monkeypatch, ntp_stub):
    monkeypatch.setattr(ntp_state, "__opts__", {"test": True}, raising=False)
    ret = ntp_state.compliant("ntp", servers=["2.2.2.2"])
    assert ret["result"] is None
    assert ntp_stub["applied"] == []


def test_ntp_applies_drift(monkeypatch, ntp_stub):
    monkeypatch.setattr(ntp_state, "__opts__", {"test": False}, raising=False)
    ret = ntp_state.compliant("ntp", servers=["2.2.2.2"])
    assert ret["changes"] == {"servers": {"old": ["1.1.1.1"], "new": ["2.2.2.2"]}}
    assert ntp_stub["applied"] == [["2.2.2.2"]]


def test_dns_applies_drift(monkeypatch):
    state = {"current": ["10.0.0.1"], "applied": []}
    monkeypatch.setattr(dns_client, "get", lambda opts, profile=None: {"servers": state["current"]})
    monkeypatch.setattr(
        dns_client, "set_", lambda opts, servers, profile=None: state["applied"].append(servers)
    )
    monkeypatch.setattr(dns_state, "__opts__", {"test": False}, raising=False)
    ret = dns_state.compliant("dns", servers=["10.0.0.2"])
    assert ret["changes"]["servers"]["new"] == ["10.0.0.2"]
    assert state["applied"] == [["10.0.0.2"]]


def test_syslog_requires_host(monkeypatch):
    monkeypatch.setattr(syslog_state, "__opts__", {"test": False}, raising=False)
    ret = syslog_state.compliant("syslog")
    assert ret["result"] is False
    assert "host is required" in ret["comment"]


def test_syslog_applies_drift(monkeypatch):
    state = {"current": {"host": "old.test", "port": 514, "insecure": False, "transport": "tcp"}, "applied": []}
    monkeypatch.setattr(syslog_client, "get", lambda opts, profile=None: {"syslog": state["current"]})
    monkeypatch.setattr(
        syslog_client,
        "set_",
        lambda opts, host, port=514, transport="tcp", insecure=False, cacert=None, profile=None: state[
            "applied"
        ].append((host, port, transport)),
    )
    monkeypatch.setattr(syslog_state, "__opts__", {"test": False}, raising=False)
    ret = syslog_state.compliant("syslog", host="new.test", port=514)
    assert ret["changes"]["syslog"]["new"]["host"] == "new.test"
    assert state["applied"] == [("new.test", 514, "tcp")]
