"""Tests for clients.vsan_disk."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vsan_disk


@pytest.fixture
def fake_host():
    host = MagicMock()
    host._moId = "host-42"  # noqa: SLF001
    host.name = "esx-0-00.example.com"
    return host


def test_host_status(opts, fake_host):
    info = MagicMock()
    info.nodeUuid = "node-uuid-1"
    info.health = "Healthy"
    info.uuid = "host-uuid-1"
    info.nodeState.state = "MASTER"
    info.memberUuid = ["m1", "m2"]
    fake_host.configManager.vsanSystem.QueryHostStatus.return_value = info

    with patch("saltext.vcf.clients.vsan_disk._find_host", return_value=fake_host):
        result = vsan_disk.host_status(opts, "esx-0-00.example.com")
    assert result["node_uuid"] == "node-uuid-1"
    assert result["health"] == "Healthy"
    assert result["members_count"] == 2


def test_host_config(opts, fake_host):
    cfg = fake_host.configManager.vsanSystem.config
    cfg.enabled = True
    cfg.clusterInfo.uuid = "cluster-uuid-1"
    cfg.clusterInfo.nodeUuid = "node-uuid-1"
    cfg.storageInfo.autoClaimStorage = False
    cfg.storageInfo.diskMapping = [MagicMock(), MagicMock()]
    cfg.faultDomainInfo.name = "rack-A"
    cfg.vsanEsaEnabled = True

    with patch("saltext.vcf.clients.vsan_disk._find_host", return_value=fake_host):
        result = vsan_disk.host_config(opts, "esx-0-00.example.com")
    assert result["enabled"] is True
    assert result["cluster_uuid"] == "cluster-uuid-1"
    assert result["disk_mapping_count"] == 2
    assert result["fault_domain"] == "rack-A"
    assert result["vsan_esa_enabled"] is True


def test_add_disks_resolves_canonical_names(opts, fake_host):
    disk1 = MagicMock(canonicalName="naa.aaa")
    disk2 = MagicMock(canonicalName="naa.bbb")
    fake_host.configManager.storageSystem.storageDeviceInfo.scsiLun = [disk1, disk2]
    task = MagicMock()
    task._moId = "task-123"  # noqa: SLF001
    fake_host.configManager.vsanSystem.AddDisks_Task.return_value = task

    with patch("saltext.vcf.clients.vsan_disk._find_host", return_value=fake_host):
        result = vsan_disk.add_disks(opts, "esx-0-00.example.com", ["naa.aaa"])

    assert result == "task-123"
    call_disks = fake_host.configManager.vsanSystem.AddDisks_Task.call_args.kwargs["disk"]
    assert call_disks == [disk1]


def test_add_disks_raises_on_missing(opts, fake_host):
    fake_host.configManager.storageSystem.storageDeviceInfo.scsiLun = []

    with patch("saltext.vcf.clients.vsan_disk._find_host", return_value=fake_host):
        with pytest.raises(LookupError):
            vsan_disk.add_disks(opts, "esx-0-00.example.com", ["naa.aaa"])
