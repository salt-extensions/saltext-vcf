"""Tests for vim_host_{storage,acceptance,hyperthreading,snmp,tcpip}."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import vim_host_acceptance
from saltext.vcf.clients import vim_host_hyperthreading
from saltext.vcf.clients import vim_host_snmp
from saltext.vcf.clients import vim_host_storage
from saltext.vcf.clients import vim_host_tcpip


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
    icm.UpdateHostImageAcceptanceLevel.assert_called_with(newAcceptanceLevel="partner")


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


# -- SCSI LUN inventory + attach/detach (vmware_esxi parity) -----------------


def _fake_lun(display="naa.001", path="vmhba0:C0:T0:L0", state="ok", ssd=True, local=True):
    lun = MagicMock()
    lun.canonicalName = display
    lun.displayName = display
    lun.devicePath = path
    lun.deviceName = f"t10.ATA____{display}"
    lun.uuid = "uuid-1"
    lun.operationalState = [state]
    d1 = MagicMock()
    d1.id = "Serial Number"
    d1.quality = "highQuality"
    lun.descriptor = [d1]
    lun.localDisk = local
    lun.ssd = ssd
    lun.physicalLocation = "0:0:0:0"
    return lun


def test_scsi_luns_full_dump(opts, host_factory):
    host_factory["host"].configManager.storageSystem.storageDeviceInfo.scsiLun = [
        _fake_lun(),
        _fake_lun("naa.002", "vmhba1:C0:T1:L1", state="off", ssd=False),
    ]
    out = vim_host_storage.scsi_luns(opts, "esx-1")
    assert len(out) == 2
    assert out[0]["state"] == "attached"
    assert out[0]["ssd"] is True
    assert out[1]["state"] == "detached"


def test_scsi_luns_filters(opts, host_factory):
    host_factory["host"].configManager.storageSystem.storageDeviceInfo.scsiLun = [
        _fake_lun(),
        _fake_lun("naa.002", "vmhba1:C0:T1:L1", state="off", ssd=False),
    ]
    assert [d["device"] for d in vim_host_storage.scsi_luns(opts, "esx-1", ssd=False)] == ["t10.ATA____naa.002"]
    assert [d["name"] for d in vim_host_storage.scsi_luns(opts, "esx-1", state="attached")] == ["naa.001"]
    assert [d["name"] for d in vim_host_storage.scsi_luns(opts, "esx-1", lun_name="vmhba1")] == ["naa.002"]
    assert vim_host_storage.scsi_luns(opts, "esx-1", disk_ids=["naa.001"]) [0]["name"] == "naa.001"


def test_list_ssds_and_non_ssds(opts, host_factory):
    host_factory["host"].configManager.storageSystem.storageDeviceInfo.scsiLun = [
        _fake_lun(),
        _fake_lun("naa.002", "vmhba1:C0:T1:L1", state="off", ssd=False),
    ]
    assert vim_host_storage.scsi_luns(opts, "esx-1", ssd=True)[0]["ssd"] is True
    assert vim_host_storage.scsi_luns(opts, "esx-1", ssd=False)[0]["ssd"] is False


def test_attach_lun_idempotent(opts, host_factory):
    ss = host_factory["host"].configManager.storageSystem
    from pyVmomi import vim as _vim

    ss.AttachScsiLun.side_effect = _vim.fault.InvalidState()
    assert vim_host_storage.attach_lun(opts, "esx-1", "naa.001") is True
    assert ss.RefreshStorageSystem.called


def test_detach_lun_missing_is_noop(opts, host_factory):
    ss = host_factory["host"].configManager.storageSystem
    from pyVmomi import vim as _vim

    ss.DetachScsiLun.side_effect = _vim.fault.NotFound()
    assert vim_host_storage.detach_lun(opts, "esx-1", "naa.001") is True
