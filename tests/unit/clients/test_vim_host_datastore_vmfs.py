"""Tests for vim_host_datastore VMFS extent inventory + mount/unmount by uuid."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_host_datastore


def _vmfs_ds(name="ds1", uuid="vmfs-uuid-1", extents=("naa.001",)):
    ds = MagicMock()
    ds.name = name
    ds._moId = f"datastore-{name}"  # noqa: SLF001
    vmfs = MagicMock()
    vmfs.name = name
    vmfs.uuid = uuid
    vmfs.local = True
    ext = MagicMock()
    ext.diskName = extents[0]
    vmfs.extent = [ext]
    ds.info.vmfs = vmfs
    return ds


@pytest.fixture
def factory(monkeypatch):
    holder = {"host": MagicMock()}
    monkeypatch.setattr(vim_host_datastore, "_find_host", lambda o, n, profile=None: holder["host"])
    return holder


def test_lun_ids_dedups_extents(opts, factory):
    factory["host"].datastore = [_vmfs_ds("ds1"), _vmfs_ds("ds2", uuid="u2", extents=("naa.001",))]
    assert vim_host_datastore.lun_ids(opts, "esxi-01") == ["naa.001"]


def test_disks_shape_and_filter(opts, factory):
    factory["host"].datastore = [_vmfs_ds("ds1"), _vmfs_ds("ds2", uuid="u2", extents=("naa.002",))]
    out = vim_host_datastore.disks(opts, "esxi-01")
    assert out == [
        {"scsi_address": "naa.001", "name": "ds1", "uuid": "vmfs-uuid-1", "local": True},
        {"scsi_address": "naa.002", "name": "ds2", "uuid": "u2", "local": True},
    ]
    assert vim_host_datastore.disks(opts, "esxi-01", disk_name="ds2")[0]["scsi_address"] == "naa.002"


def test_mount_vmfs_happy_path(opts, factory):
    storage = factory["host"].configManager.storageSystem
    steps = vim_host_datastore.mount_vmfs(
        opts, "esxi-01", "vmfs-uuid-1", lun_canonical_name="naa.001"
    )
    storage.AttachScsiLun.assert_called_once_with(lunCanonicalName="naa.001")
    storage.MountVmfsVolume.assert_called_once_with("vmfs-uuid-1")
    assert any("attached disk naa.001" in s for s in steps)


def test_mount_vmfs_resolves_unresolved(opts, factory):
    storage = factory["host"].configManager.storageSystem
    storage.MountVmfsVolume.side_effect = vim.fault.NotFound()
    unresolved = MagicMock()
    unresolved.vmfsUuid = "vmfs-uuid-1"
    unresolved.resolveStatus.resolvable = True
    ext = MagicMock()
    ext.devicePath = "/vmfs/devices/disks/naa.001"
    unresolved.extent = [ext]
    storage.QueryUnresolvedVmfsVolume.return_value = [unresolved]
    steps = vim_host_datastore.mount_vmfs(opts, "esxi-01", "vmfs-uuid-1")
    storage.ResolveMultipleUnresolvedVmfsVolumes.assert_called_once()
    spec = storage.ResolveMultipleUnresolvedVmfsVolumes.call_args.args[0][0]
    assert spec.uuidResolution == "forceMounted"
    assert spec.extentDevicePath == ["/vmfs/devices/disks/naa.001"]
    assert any("resolved" in s for s in steps)


def test_mount_vmfs_unresolvable_raises(opts, factory):
    storage = factory["host"].configManager.storageSystem
    storage.MountVmfsVolume.side_effect = vim.fault.NotFound()
    unresolved = MagicMock()
    unresolved.vmfsUuid = "vmfs-uuid-1"
    unresolved.resolveStatus.resolvable = False
    storage.QueryUnresolvedVmfsVolume.return_value = [unresolved]
    with pytest.raises(RuntimeError):
        vim_host_datastore.mount_vmfs(opts, "esxi-01", "vmfs-uuid-1")


def test_mount_vmfs_already_mounted(opts, factory):
    storage = factory["host"].configManager.storageSystem
    storage.MountVmfsVolume.side_effect = vim.fault.InvalidState()
    steps = vim_host_datastore.mount_vmfs(opts, "esxi-01", "vmfs-uuid-1")
    assert any("already mounted" in s for s in steps)


def test_unmount_vmfs_and_detach(opts, factory):
    storage = factory["host"].configManager.storageSystem
    mount_info = MagicMock()
    vol = MagicMock()
    vol.uuid = "vmfs-uuid-1"
    ext = MagicMock()
    ext.diskName = "naa.001"
    vol.extent = [ext]
    mount_info.volume = vol
    storage.fileSystemVolumeInfo.mountInfo = [mount_info]
    steps = vim_host_datastore.unmount_vmfs(opts, "esxi-01", "vmfs-uuid-1")
    storage.UnmountVmfsVolume.assert_called_once_with("vmfs-uuid-1")
    storage.DetachScsiLun.assert_called_once_with(lunCanonicalName="naa.001")
    assert any("unmounted" in s for s in steps)


def test_unmount_vmfs_unknown_uuid_raises(opts, factory):
    storage = factory["host"].configManager.storageSystem
    storage.fileSystemVolumeInfo.mountInfo = []
    with pytest.raises(LookupError):
        vim_host_datastore.unmount_vmfs(opts, "esxi-01", "nope")
