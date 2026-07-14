"""Tests for modules.vcf_esxi_firewall."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_esxi_firewall as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def _ruleset(key, enabled=True, all_ip=True, ip_addresses=()):
    rs = MagicMock()
    rs.key = key
    rs.label = key
    rs.enabled = enabled
    rs.allowedHosts.allIp = all_ip
    rs.allowedHosts.ipAddress = list(ip_addresses)
    return rs


def _fake_host(rulesets=()):
    host = MagicMock()
    host.configManager.firewallSystem.firewallInfo.ruleset = list(rulesets)
    return host


def test_list():
    host = _fake_host()
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.list_() == {}


def test_get():
    rs = _ruleset("sshServer", enabled=True, all_ip=True)
    host = _fake_host([rs])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.get("sshServer")
    assert result["enabled"] is True
    assert result["allowed_hosts"] == {"all_ip": True, "ip_addresses": []}


def test_set_enabled():
    rs = _ruleset("sshServer", enabled=False)
    host = _fake_host([rs])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_enabled("sshServer", False)
    host.configManager.firewallSystem.DisableRuleset.assert_called_once_with(id="sshServer")


def test_enabled_true():
    host = _fake_host()
    host.configManager.firewallSystem.firewallInfo.defaultPolicy.incomingBlocked = True
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.enabled() is True


def test_enabled_false():
    host = _fake_host()
    host.configManager.firewallSystem.firewallInfo.defaultPolicy.incomingBlocked = False
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.enabled() is False


def test_set_global_enabled_disables():
    host = _fake_host()
    host.configManager.firewallSystem.firewallInfo.defaultPolicy.incomingBlocked = False
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.set_global_enabled(False) is False
    call = host.configManager.firewallSystem.UpdateDefaultPolicy.call_args
    assert call.kwargs["defaultPolicy"].incomingBlocked is False
    assert call.kwargs["defaultPolicy"].outgoingBlocked is False


def test_set_global_enabled_enables():
    host = _fake_host()
    host.configManager.firewallSystem.firewallInfo.defaultPolicy.incomingBlocked = True
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.set_global_enabled(True) is True
    call = host.configManager.firewallSystem.UpdateDefaultPolicy.call_args
    assert call.kwargs["defaultPolicy"].incomingBlocked is True
    assert call.kwargs["defaultPolicy"].outgoingBlocked is True


def test_set_allowed_ips():
    rs = _ruleset("sshServer", all_ip=False, ip_addresses=["10.0.0.0/24"])
    host = _fake_host([rs])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_allowed_ips("sshServer", ["10.0.0.0/24"], all_ip=False)
    call = host.configManager.firewallSystem.UpdateRuleset.call_args
    assert call.kwargs["id"] == "sshServer"
    assert call.kwargs["spec"].allowedHosts.allIp is False
    assert list(call.kwargs["spec"].allowedHosts.ipAddress) == ["10.0.0.0/24"]
