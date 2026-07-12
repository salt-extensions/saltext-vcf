"""Tests for states.vcf_esxi_firewall."""

import pytest

from saltext.vcf.clients import esxi_firewall as c
from saltext.vcf.states import vcf_esxi_firewall as st


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


# ---------------------------------------------------------------------------
# global_enabled
# ---------------------------------------------------------------------------


@pytest.fixture
def global_stub(monkeypatch):
    state = {"current": True, "calls": []}
    monkeypatch.setattr(c, "enabled", lambda opts, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "set_global_enabled",
        lambda opts, enabled, profile=None: state["calls"].append(("set", enabled)) or enabled,
    )
    return state


def test_global_enabled_already_matches(global_stub):
    global_stub["current"] = True
    ret = st.global_enabled("host-firewall", enabled=True)
    assert ret["changes"] == {}
    assert global_stub["calls"] == []


def test_global_enabled_disables(global_stub):
    global_stub["current"] = True
    ret = st.global_enabled("host-firewall", enabled=False)
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert global_stub["calls"] == [("set", False)]


def test_global_enabled_enables(global_stub):
    global_stub["current"] = False
    ret = st.global_enabled("host-firewall", enabled=True)
    assert ret["changes"] == {"enabled": {"old": False, "new": True}}
    assert global_stub["calls"] == [("set", True)]


def test_global_enabled_test_mode(monkeypatch, global_stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    global_stub["current"] = True
    ret = st.global_enabled("host-firewall", enabled=False)
    assert ret["result"] is None
    assert global_stub["calls"] == []
