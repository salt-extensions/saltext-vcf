"""Tests for states.vmware_esxi_firewall."""

import pytest

from saltext.vmware.clients import esxi_firewall as c
from saltext.vmware.states import vmware_esxi_firewall as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"rule": None, "calls": []}

    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: state["rule"])
    monkeypatch.setattr(
        c,
        "set_enabled",
        lambda opts, name, enabled, profile=None: state["calls"].append(("enabled", name, enabled)),
    )
    monkeypatch.setattr(
        c,
        "set_allowed_ips",
        lambda opts, name, allowed, all_ip=False, profile=None: state["calls"].append(
            ("ips", name, list(allowed), all_ip)
        ),
    )
    return state


def test_already_matches(stub):
    stub["rule"] = {
        "enabled": True,
        "allowed_hosts": {"all_ip": False, "ip_addresses": ["10.0.0.0/24"]},
    }
    ret = st.rule_enabled("sshServer", enabled=True, allowed_ips=["10.0.0.0/24"])
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_enable_disabled_rule(stub):
    stub["rule"] = {
        "enabled": False,
        "allowed_hosts": {"all_ip": True, "ip_addresses": []},
    }
    ret = st.rule_enabled("sshServer", enabled=True)
    assert ret["changes"]["enabled"] == {"old": False, "new": True}
    assert ("enabled", "sshServer", True) in stub["calls"]


def test_allowed_ips_change(stub):
    stub["rule"] = {
        "enabled": True,
        "allowed_hosts": {"all_ip": True, "ip_addresses": []},
    }
    ret = st.rule_enabled("sshServer", enabled=True, allowed_ips=["10.0.0.0/24"], all_ip=False)
    assert ret["changes"]["allowed_hosts"]["new"] == {
        "all_ip": False,
        "ip_addresses": ["10.0.0.0/24"],
    }
    assert ("ips", "sshServer", ["10.0.0.0/24"], False) in stub["calls"]


def test_missing_rule(stub):
    stub["rule"] = None
    ret = st.rule_enabled("nope")
    assert ret["result"] is False


def test_disable_shortcut(stub):
    stub["rule"] = {"enabled": True, "allowed_hosts": {}}
    ret = st.rule_disabled("sshServer")
    assert ret["changes"]["enabled"] == {"old": True, "new": False}


def test_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["rule"] = {"enabled": False, "allowed_hosts": {}}
    ret = st.rule_enabled("sshServer", enabled=True)
    assert ret["result"] is None
    assert stub["calls"] == []
