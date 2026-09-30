"""Tests for clients.vim_host_firewall (vCenter-routed rulesets)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_host_firewall


def _ruleset(name="CIMHttpServer", enabled=True, all_ip=True):
    r = MagicMock()
    r.key = name
    r.service = None
    r.enabled = enabled
    r.allowedHosts.allIp = all_ip
    r.allowedHosts.ipAddress = ["10.0.0.5"]
    net = MagicMock()
    net.network = "192.168.0.0"
    net.prefixLength = 24
    r.allowedHosts.ipNetwork = [net]
    rule = MagicMock()
    rule.port = "80"
    rule.endPort = 80
    rule.direction = "inbound"
    rule.portType = "tcp"
    rule.protocol = "tcp"
    r.rule = [rule]
    return r


@pytest.fixture
def factory(monkeypatch):
    host = MagicMock()
    host.name = "esxi-01"
    fw = host.configManager.firewallSystem
    fw.firewallInfo.ruleset = [_ruleset()]
    monkeypatch.setattr(vim_host_firewall, "_resolve", lambda o, n, profile=None: host)
    return {"host": host, "fw": fw}


def test_get_all(opts, factory):
    out = vim_host_firewall.get_all(opts, "esxi-01")
    assert "CIMHttpServer" in out
    assert out["CIMHttpServer"]["enabled"] is True
    assert out["CIMHttpServer"]["allowed_hosts"]["ip_network"] == ["192.168.0.0/24"]
    assert out["CIMHttpServer"]["rule"][0]["port"] == "80"


def test_get_missing_raises(opts, factory):
    with pytest.raises(LookupError):
        vim_host_firewall.get(opts, "esxi-01", "NoSuchRuleset")


def test_set_enabled_toggles(opts, factory):
    assert vim_host_firewall.set_enabled(opts, "esxi-01", "CIMHttpServer", False) is False
    factory["fw"].DisableRuleset.assert_called_once_with(id="CIMHttpServer")


def test_set_config_full_shape(opts, factory):
    cfg = {
        "name": "CIMHttpServer",
        "enabled": False,
        "allowed_hosts": {"all_ip": False, "ip_address": ["10.1.1.1"], "ip_network": ["10.2.0.0/16"]},
    }
    out = vim_host_firewall.set_config(opts, "esxi-01", cfg)
    factory["fw"].DisableRuleset.assert_called_once_with(id="CIMHttpServer")
    kwargs = factory["fw"].UpdateRuleset.call_args.kwargs
    assert kwargs["id"] == "CIMHttpServer"
    ah = kwargs["spec"].allowedHosts
    assert ah.allIp is False
    assert ah.ipAddress == ["10.1.1.1"]
    assert ah.ipNetwork[0].prefixLength == 16
    assert out["name"] == "CIMHttpServer"


def test_set_all_configs(opts, factory):
    cfgs = [{"name": "CIMHttpServer", "enabled": False}]
    out = vim_host_firewall.set_all_configs(opts, "esxi-01", cfgs)
    assert len(out) == 1
