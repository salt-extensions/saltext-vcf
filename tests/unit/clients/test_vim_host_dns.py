"""Tests for clients.vim_host_dns."""

from unittest.mock import MagicMock

import pytest

from saltext.vmware.clients import vim_host_dns


def _dns(dhcp=False, hostname="esx-1", domain="example.com", servers=None, search=None, vnic=None):
    cfg = MagicMock()
    cfg.dhcp = dhcp
    cfg.hostName = hostname
    cfg.domainName = domain
    cfg.address = servers or []
    cfg.searchDomain = search or []
    cfg.virtualNicDevice = vnic
    return cfg


@pytest.fixture
def host_factory(monkeypatch):
    host = MagicMock()
    host.config.network.dnsConfig = _dns(servers=["10.0.0.1"], search=["example.com"])
    host.name = "esx-1"
    monkeypatch.setattr(vim_host_dns, "_host", lambda opts, h, profile=None: host)
    return host


def test_get(opts, host_factory):
    out = vim_host_dns.get(opts, "esx-1")
    assert out["hostname"] == "esx-1"
    assert out["servers"] == ["10.0.0.1"]
    assert out["search_domains"] == ["example.com"]
    assert out["dhcp"] is False


def test_set_servers_preserves_other_fields(opts, host_factory):
    net = host_factory.configManager.networkSystem
    vim_host_dns.set_(opts, "esx-1", servers=["10.0.0.2", "10.0.0.3"])
    net.UpdateDnsConfig.assert_called_once()
    spec = net.UpdateDnsConfig.call_args.kwargs["config"]
    assert list(spec.address) == ["10.0.0.2", "10.0.0.3"]
    # hostname/domain/search unchanged
    assert spec.hostName == "esx-1"
    assert spec.searchDomain == ["example.com"]


def test_set_dhcp_only(opts, host_factory):
    net = host_factory.configManager.networkSystem
    vim_host_dns.set_(opts, "esx-1", dhcp=True)
    spec = net.UpdateDnsConfig.call_args.kwargs["config"]
    assert spec.dhcp is True
