"""Tests for the vcf_vim_host_firewall state module."""

import pytest

from saltext.vcf.clients import vim_host_firewall as c
from saltext.vcf.states import vcf_vim_host_firewall as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


_RULESET = {
    "name": "CIMHttpServer",
    "enabled": True,
    "allowed_hosts": {"all_ip": True, "ip_address": [], "ip_network": []},
    "rule": [],
}


def test_firewall_config_bool_noop(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, h, n, profile=None: dict(_RULESET))
    ret = st.firewall_config("CIMHttpServer", "esxi-01", True)
    assert ret["changes"] == {}


def test_firewall_config_disables(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, h, n, profile=None: dict(_RULESET))
    captured = {}
    monkeypatch.setattr(c, "set_config", lambda o, h, cfg, profile=None: captured.update(cfg))
    ret = st.firewall_config("CIMHttpServer", "esxi-01", False)
    assert ret["changes"]["enabled"] == (True, False)
    assert captured["enabled"] is False


def test_firewall_config_missing_ruleset(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, h, n, profile=None: None)
    ret = st.firewall_config("Nope", "esxi-01", True)
    assert ret["result"] is False


def test_firewall_config_test_mode(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, h, n, profile=None: dict(_RULESET))
    monkeypatch.setattr(c, "set_config", lambda *a, **kw: pytest.fail("must not set"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.firewall_config("CIMHttpServer", "esxi-01", False)
    assert ret["result"] is None


# ---------- firewall_configs (batch) ----------


def test_firewall_configs_noop(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_all",
        lambda o, h, profile=None: {"sshServer": dict(_RULESET), "sshClient": dict(_RULESET)},
    )
    ret = st.firewall_configs("fw", "esxi-01", {"sshServer": True, "sshClient": True})
    assert ret["changes"] == {}


def test_firewall_configs_batch_drift(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_all",
        lambda o, h, profile=None: {
            "sshServer": dict(_RULESET),
            "sshClient": {
                "name": "sshClient",
                "enabled": False,
                "allowed_hosts": {"all_ip": True, "ip_address": [], "ip_network": []},
                "rule": [],
            },
        },
    )
    captured = []
    monkeypatch.setattr(c, "set_all_configs", lambda o, h, cfgs, profile=None: captured.extend(cfgs))
    ret = st.firewall_configs("fw", "esxi-01", {"sshServer": True, "sshClient": True})
    assert ret["result"] is True
    assert "sshClient" in ret["changes"]
    assert captured and captured[0]["name"] == "sshServer"
