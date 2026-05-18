"""Tests for clients.vim_vm_migrate (A5)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_migrate


def _fake_vm():
    vm = MagicMock()
    vm._moId = "vm-100"
    vm.MigrateVM_Task.return_value = MagicMock(_moId="task-mig")
    vm.RelocateVM_Task.return_value = MagicMock(_moId="task-rel")
    return vm


@pytest.fixture
def factory(monkeypatch):
    holder = {
        "vm": _fake_vm(),
        "host": vim.HostSystem("host-1", None),
        "pool": vim.ResourcePool("rp-1", None),
        "ds": vim.Datastore("ds-1", None),
        "folder": vim.Folder("f-1", None),
    }
    type_map = {
        vim.HostSystem: holder["host"],
        vim.ResourcePool: holder["pool"],
        vim.Datastore: holder["ds"],
        vim.Folder: holder["folder"],
    }

    def patcher_vm(opts, vm_id, profile=None):
        return holder["vm"]

    def patcher_find(opts, vim_type, name, profile=None):
        return type_map[vim_type]

    monkeypatch.setattr(vim_vm_migrate, "_vm", patcher_vm)
    monkeypatch.setattr(vim_vm_migrate, "_find_by_type", patcher_find)
    return holder


def test_migrate_requires_target(factory, opts):
    with pytest.raises(ValueError):
        vim_vm_migrate.migrate(opts, "vm-100")


def test_migrate_with_host(factory, opts):
    assert vim_vm_migrate.migrate(opts, "vm-100", host="esxi-2") == "task-mig"
    factory["vm"].MigrateVM_Task.assert_called_once()
    kwargs = factory["vm"].MigrateVM_Task.call_args.kwargs
    assert kwargs["host"] is factory["host"]
    assert kwargs["pool"] is None
    assert kwargs["priority"] == vim.VirtualMachine.MovePriority.defaultPriority
    assert kwargs["state"] is None


def test_migrate_high_priority(factory, opts):
    vim_vm_migrate.migrate(opts, "vm-100", host="esxi-2", priority="high")
    kwargs = factory["vm"].MigrateVM_Task.call_args.kwargs
    assert kwargs["priority"] == vim.VirtualMachine.MovePriority.highPriority


def test_migrate_with_state_filter(factory, opts):
    vim_vm_migrate.migrate(opts, "vm-100", host="esxi-2", state="poweredOn")
    kwargs = factory["vm"].MigrateVM_Task.call_args.kwargs
    assert kwargs["state"] == vim.VirtualMachine.PowerState.poweredOn


def test_relocate_builds_spec(factory, opts):
    out = vim_vm_migrate.relocate(
        opts, "vm-100", host="esxi-2", datastore="ds-1", folder="f-1", resource_pool="rp-1"
    )
    assert out == "task-rel"
    factory["vm"].RelocateVM_Task.assert_called_once()
    call = factory["vm"].RelocateVM_Task.call_args
    spec = call.kwargs["spec"]
    assert isinstance(spec, vim.vm.RelocateSpec)
    assert spec.host is factory["host"]
    assert spec.datastore is factory["ds"]
    assert spec.folder is factory["folder"]
    assert spec.pool is factory["pool"]


def test_relocate_with_disk_format(factory, opts):
    vim_vm_migrate.relocate(opts, "vm-100", host="esxi-2", disk_format="sparse")
    spec = factory["vm"].RelocateVM_Task.call_args.kwargs["spec"]
    assert spec.transform == "sparse"


def test_module_wrappers_delegate(factory, opts, monkeypatch):
    from saltext.vcf.modules import vcf_vim_vm_migrate as m

    monkeypatch.setattr(m, "__opts__", opts, raising=False)
    assert m.migrate("vm-100", host="esxi-2") == "task-mig"
    assert m.relocate("vm-100", datastore="ds-1") == "task-rel"
