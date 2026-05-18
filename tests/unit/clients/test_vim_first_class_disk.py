"""Tests for clients.vim_first_class_disk (FCD / vStorageObject)."""

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_first_class_disk


def _make_fcd(fcd_id="vslm-1", name="disk", capacity_mb=1024, keep=False, ds_moid="ds-1"):
    obj = MagicMock()
    obj.config.id.id = fcd_id
    obj.config.name = name
    obj.config.capacityInMB = capacity_mb
    obj.config.createTime = datetime(2026, 5, 12, tzinfo=timezone.utc)
    obj.config.keepAfterDeleteVm = keep
    obj.config.consumptionType = ["disk"]
    obj.config.consumerId = []
    obj.config.iofilter = []
    obj.config.backing.datastore._moId = ds_moid
    obj.config.backing.filePath = f"[{ds_moid}] disks/{name}.vmdk"
    obj.config.backing.provisioningType = "thin"
    return obj


@pytest.fixture
def env(monkeypatch):
    # Real vim.Datastore so pyVmomi type-checking in CreateSpec.backingSpec passes.
    ds = vim.Datastore("ds-1", None)
    vsom = MagicMock()
    monkeypatch.setattr(vim_first_class_disk, "_find_datastore", lambda o, n, profile=None: ds)
    monkeypatch.setattr(vim_first_class_disk, "_vsom", lambda o, profile=None: vsom)
    return {"ds": ds, "vsom": vsom}


def test_list_returns_dicts(opts, env):
    fcd_a = _make_fcd("vslm-1", "disk-a", capacity_mb=2048)
    fcd_b = _make_fcd("vslm-2", "disk-b", capacity_mb=4096, keep=True)
    env["vsom"].ListVStorageObject.return_value = [
        vim.vslm.ID(id="vslm-1"),
        vim.vslm.ID(id="vslm-2"),
    ]
    env["vsom"].RetrieveVStorageObject.side_effect = [fcd_a, fcd_b]
    out = vim_first_class_disk.list_(opts, "datastore-1")
    assert {d["name"] for d in out} == {"disk-a", "disk-b"}
    assert out[1]["keep_after_delete_vm"] is True
    assert out[0]["capacity_bytes"] == 2048 * 1024 * 1024


def test_list_skips_missing(opts, env):
    env["vsom"].ListVStorageObject.return_value = [
        vim.vslm.ID(id="vslm-1"),
        vim.vslm.ID(id="missing"),
    ]
    env["vsom"].RetrieveVStorageObject.side_effect = [
        _make_fcd("vslm-1", "ok"),
        vim.fault.NotFound(),
    ]
    out = vim_first_class_disk.list_(opts, "datastore-1")
    assert len(out) == 1
    assert out[0]["name"] == "ok"


def test_get_returns_dict(opts, env):
    env["vsom"].RetrieveVStorageObject.return_value = _make_fcd("vslm-1", "disk")
    out = vim_first_class_disk.get(opts, "vslm-1", "datastore-1")
    assert out["id"] == "vslm-1"
    env["vsom"].RetrieveVStorageObject.assert_called_once()


def test_get_or_none_404(opts, env):
    env["vsom"].RetrieveVStorageObject.side_effect = vim.fault.NotFound()
    assert vim_first_class_disk.get_or_none(opts, "missing", "datastore-1") is None


def test_create_returns_task(opts, env):
    env["vsom"].CreateDisk_Task.return_value = MagicMock(_moId="task-c")
    out = vim_first_class_disk.create(opts, "disk", "datastore-1", capacity_gb=10)
    assert out == "task-c"
    spec = env["vsom"].CreateDisk_Task.call_args.kwargs["spec"]
    assert spec.name == "disk"
    assert spec.capacityInMB == 10 * 1024
    assert spec.backingSpec.provisioningType == "thin"


def test_create_with_keep_flag(opts, env):
    env["vsom"].CreateDisk_Task.return_value = MagicMock(_moId="task-c")
    vim_first_class_disk.create(
        opts, "disk", "datastore-1", capacity_gb=5, keep_after_delete_vm=True
    )
    spec = env["vsom"].CreateDisk_Task.call_args.kwargs["spec"]
    assert spec.keepAfterDeleteVm is True


def test_delete_returns_task(opts, env):
    env["vsom"].DeleteVStorageObject_Task.return_value = MagicMock(_moId="task-del")
    out = vim_first_class_disk.delete(opts, "vslm-1", "datastore-1")
    assert out == "task-del"


def test_rename(opts, env):
    assert vim_first_class_disk.rename(opts, "vslm-1", "datastore-1", "newname") is True
    env["vsom"].RenameVStorageObject.assert_called_once()
    kwargs = env["vsom"].RenameVStorageObject.call_args.kwargs
    assert kwargs["id"].id == "vslm-1"
    assert kwargs["name"] == "newname"


def test_extend_returns_task(opts, env):
    env["vsom"].ExtendDisk_Task.return_value = MagicMock(_moId="task-grow")
    out = vim_first_class_disk.extend(opts, "vslm-1", "datastore-1", new_capacity_gb=50)
    assert out == "task-grow"
    kwargs = env["vsom"].ExtendDisk_Task.call_args.kwargs
    assert kwargs["newCapacityInMB"] == 50 * 1024


def test_set_keep_after_delete_vm_on(opts, env):
    assert (
        vim_first_class_disk.set_keep_after_delete_vm(opts, "vslm-1", "datastore-1", True) is True
    )
    env["vsom"].SetVStorageObjectControlFlags.assert_called_once()
    env["vsom"].ClearVStorageObjectControlFlags.assert_not_called()


def test_set_keep_after_delete_vm_off(opts, env):
    vim_first_class_disk.set_keep_after_delete_vm(opts, "vslm-1", "datastore-1", False)
    env["vsom"].ClearVStorageObjectControlFlags.assert_called_once()


def test_attach_to_vm_returns_task(opts, env, monkeypatch):
    vm = MagicMock()
    vm.AttachDisk_Task.return_value = MagicMock(_moId="task-att")
    monkeypatch.setattr(vim_first_class_disk, "_find_vm", lambda o, n, profile=None: vm)
    out = vim_first_class_disk.attach_to_vm(opts, "myvm", "vslm-1", "datastore-1")
    assert out == "task-att"


def test_detach_from_vm_returns_task(opts, env, monkeypatch):
    vm = MagicMock()
    vm.DetachDisk_Task.return_value = MagicMock(_moId="task-det")
    monkeypatch.setattr(vim_first_class_disk, "_find_vm", lambda o, n, profile=None: vm)
    out = vim_first_class_disk.detach_from_vm(opts, "myvm", "vslm-1")
    assert out == "task-det"


def test_register(opts, env):
    env["vsom"].RegisterDisk.return_value = _make_fcd("vslm-1", "imported")
    out = vim_first_class_disk.register(opts, "datastore-1", "[ds-1] disks/old.vmdk", "imported")
    assert out["name"] == "imported"
