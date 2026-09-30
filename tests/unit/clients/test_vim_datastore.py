"""Tests for clients.vim_datastore (datastore lifecycle via SOAP)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_datastore


def _fake_ds(name="ds1", moid="datastore-1", maintenance="normal", vmfs_uuid="uuid-1"):
    ds = MagicMock()
    ds._moId = moid  # noqa: SLF001
    ds.name = name
    ds.summary.name = name
    ds.summary.type = "VMFS"
    ds.summary.accessible = True
    ds.summary.capacity = 1000
    ds.summary.freeSpace = 500
    ds.summary.maintenanceMode = maintenance
    ds.summary.multipleHostAccess = False
    ds.summary.uncommitted = 10
    ds.summary.url = "/vmfs/volumes/ds1"
    vmfs = MagicMock()
    vmfs.uuid = vmfs_uuid
    vmfs.name = name
    vmfs.local = True
    ext = MagicMock()
    ext.diskName = "naa.001"
    vmfs.extent = [ext]
    ds.info.vmfs = vmfs
    ds.DatastoreEnterMaintenanceMode.return_value = True
    ds.DatastoreExitMaintenanceMode_Task.return_value = MagicMock(_moId="task-mm-1")
    return ds


@pytest.fixture
def factory(monkeypatch):
    holder = {"ds": _fake_ds()}
    monkeypatch.setattr(vim_datastore, "_find_datastore", lambda o, n, profile=None: holder["ds"])
    return holder


def test_get_shape(opts, factory, monkeypatch):
    monkeypatch.setattr(
        "saltext.vcf.utils.vim.content", lambda o, profile=None: MagicMock(rootFolder=MagicMock())
    )
    out = vim_datastore.get(opts, "ds1")
    assert out["name"] == "ds1"
    assert out["maintenance_mode"] == "normal"
    assert out["vmfs"]["uuid"] == "uuid-1"
    assert out["vmfs"]["extents"] == ["naa.001"]
    assert out["uncommitted"] == 10


def test_get_or_none_missing(opts, monkeypatch):
    monkeypatch.setattr(
        vim_datastore, "_find_datastore", lambda o, n, profile=None: (_ for _ in ()).throw(LookupError("x"))
    )
    assert vim_datastore.get_or_none(opts, "nope") is None


def test_enter_maintenance(opts, factory):
    out = vim_datastore.enter_maintenance(opts, "ds1")
    assert out["maintenanceMode"] == "inMaintenance"
    factory["ds"].DatastoreEnterMaintenanceMode.assert_called_once()


def test_enter_maintenance_failure(opts, factory):
    factory["ds"].DatastoreEnterMaintenanceMode.return_value = False
    out = vim_datastore.enter_maintenance(opts, "ds1")
    assert out["maintenanceMode"] == "failed to enter maintenance mode"


def test_exit_maintenance(opts, factory, monkeypatch):
    monkeypatch.setattr("saltext.vcf.utils.vim.wait_for_task", lambda t, **kw: None)
    out = vim_datastore.exit_maintenance(opts, "ds1")
    assert out["maintenanceMode"] == "normal"


def test_disk_partitions(opts, monkeypatch):
    host = MagicMock()
    storage = host.configManager.storageSystem
    lun = MagicMock()
    lun.canonicalName = "naa.001"
    lun.devicePath = "/vmfs/devices/disks/naa.001"
    storage.storageDeviceInfo.scsiLun = [lun]
    part_info = MagicMock()
    spec_p = MagicMock()
    spec_p.partition = 1
    spec_p.startSector = 2048
    spec_p.endSector = 4095
    spec_p.type = "VMFS"
    part_info.spec.partitionFormat = "GPT"
    part_info.spec.partition = [spec_p]
    layout_p = MagicMock()
    layout_p.partition = 1
    layout_p.start.block = 2048
    layout_p.start.blockSize = 512
    layout_p.end.block = 4095
    part_info.layout.partition = [layout_p]
    storage.RetrieveDiskPartitionInfo.return_value = [part_info]
    from saltext.vcf.clients import vim_host_storage

    monkeypatch.setattr(vim_host_storage, "_host", lambda o, n, profile=None: host)
    monkeypatch.setattr(vim_host_storage, "_ss", lambda h: h.configManager.storageSystem)
    out = vim_datastore.disk_partitions(opts, "esxi-01", disk_id="naa.001")
    assert out[0]["partition"] == 1
    assert out[0]["sectors"] == 2048
    assert out[0]["format"] == "GPT"
