"""Tests for vim_host_{storage,acceptance,hyperthreading,snmp,tcpip}."""

from unittest.mock import MagicMock

import pytest

from saltext.vmware.clients import vim_host_acceptance
from saltext.vmware.clients import vim_host_hyperthreading
from saltext.vmware.clients import vim_host_snmp
from saltext.vmware.clients import vim_host_storage
from saltext.vmware.clients import vim_host_tcpip


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"host": MagicMock()}

    def patched(opts, n, profile=None):
        return holder["host"]

    monkeypatch.setattr(vim_host_storage, "_host", patched)
    monkeypatch.setattr(vim_host_acceptance, "_host", patched)
    monkeypatch.setattr(vim_host_hyperthreading, "_host", patched)
    monkeypatch.setattr(vim_host_snmp, "_host", patched)
    monkeypatch.setattr(vim_host_tcpip, "_host", patched)
    return holder


# -- storage rescan ----------------------------------------------------------


def test_rescan_all_hba(opts, host_factory):
    ss = host_factory["host"].configManager.storageSystem
    assert vim_host_storage.rescan_all_hba(opts, "esx-1") is True
    ss.RescanAllHba.assert_called_once()


def test_rescan_vmfs(opts, host_factory):
    ss = host_factory["host"].configManager.storageSystem
    vim_host_storage.rescan_vmfs(opts, "esx-1")
    ss.RescanVmfs.assert_called_once()


def test_refresh(opts, host_factory):
    ss = host_factory["host"].configManager.storageSystem
    vim_host_storage.refresh(opts, "esx-1")
    ss.RefreshStorageSystem.assert_called_once()


# -- acceptance level --------------------------------------------------------


def test_acceptance_get(opts, host_factory):
    icm = host_factory["host"].configManager.imageConfigManager
    icm.HostImageConfigGetAcceptance.return_value = "community"
    assert vim_host_acceptance.get(opts, "esx-1") == "community"


def test_acceptance_set(opts, host_factory):
    icm = host_factory["host"].configManager.imageConfigManager
    assert vim_host_acceptance.set_(opts, "esx-1", "partner") == "partner"
    icm.HostImageConfigSetAcceptance.assert_called_with(newAcceptanceLevel="partner")


# -- hyperthreading ----------------------------------------------------------


def test_hyperthreading_get(opts, host_factory):
    cs = host_factory["host"].configManager.cpuScheduler
    cs.hyperthreadInfo.available = True
    cs.hyperthreadInfo.active = True
    cs.hyperthreadInfo.config = False
    out = vim_host_hyperthreading.get(opts, "esx-1")
    assert out == {"available": True, "active": True, "config": False}


def test_hyperthreading_enable(opts, host_factory):
    cs = host_factory["host"].configManager.cpuScheduler
    assert vim_host_hyperthreading.enable(opts, "esx-1") is True
    cs.EnableHyperThreading.assert_called_once()


def test_hyperthreading_disable(opts, host_factory):
    cs = host_factory["host"].configManager.cpuScheduler
    vim_host_hyperthreading.disable(opts, "esx-1")
    cs.DisableHyperThreading.assert_called_once()


# -- SNMP --------------------------------------------------------------------


def _fake_snmp_cfg(enabled=False, port=161, communities=None, trap_targets=None):
    cfg = MagicMock()
    cfg.enabled = enabled
    cfg.port = port
    cfg.readOnlyCommunities = communities or []
    cfg.trapTargets = trap_targets or []
    cfg.option = []
    return cfg


def test_snmp_get(opts, host_factory):
    snmp = host_factory["host"].configManager.snmpSystem
    snmp.configuration = _fake_snmp_cfg(enabled=True, communities=["public"])
    out = vim_host_snmp.get(opts, "esx-1")
    assert out["enabled"] is True
    assert out["read_only_communities"] == ["public"]


def test_snmp_set_preserves_unchanged(opts, host_factory):
    snmp = host_factory["host"].configManager.snmpSystem
    snmp.configuration = _fake_snmp_cfg(enabled=False, port=161, communities=["old"])
    # After ReconfigureSnmpAgent, get() returns updated state via the same configuration mock
    snmp.configuration.enabled = True
    vim_host_snmp.set_(opts, "esx-1", enabled=True)
    snmp.ReconfigureSnmpAgent.assert_called_once()
    spec = snmp.ReconfigureSnmpAgent.call_args.kwargs["spec"]
    assert spec.enabled is True
    assert spec.port == 161
    assert list(spec.readOnlyCommunities) == ["old"]


# -- TCP/IP stacks -----------------------------------------------------------


def _fake_stack(key="defaultTcpipStack", dns=("10.0.0.2",)):
    s = MagicMock()
    s.key = key
    s.name = key
    s.ipV6Enabled = True
    s.dnsConfig.hostName = "esx-1"
    s.dnsConfig.domainName = "example.com"
    s.dnsConfig.address = list(dns)
    s.dnsConfig.searchDomain = []
    return s


def test_tcpip_list_and_get(opts, host_factory):
    stack = _fake_stack()
    host_factory["host"].config.network.netStackInstance = [stack]
    out = vim_host_tcpip.list_(opts, "esx-1")
    assert out[0]["key"] == "defaultTcpipStack"
    assert out[0]["dns_config"]["servers"] == ["10.0.0.2"]
    assert vim_host_tcpip.get(opts, "esx-1", "defaultTcpipStack")["key"] == "defaultTcpipStack"


def test_tcpip_get_or_none(opts, host_factory):
    host_factory["host"].config.network.netStackInstance = []
    assert vim_host_tcpip.get_or_none(opts, "esx-1", "missing") is None


def test_tcpip_update_dns(opts, host_factory):
    stack = _fake_stack()
    host_factory["host"].config.network.netStackInstance = [stack]
    net = host_factory["host"].configManager.networkSystem
    vim_host_tcpip.update(opts, "esx-1", "defaultTcpipStack", dns_servers=["10.0.0.99"])
    net.UpdateNetStackInstance.assert_called_once()
    spec = net.UpdateNetStackInstance.call_args.kwargs["netStackInstance"]
    assert spec.key == "defaultTcpipStack"
    assert list(spec.dnsConfig.address) == ["10.0.0.99"]
