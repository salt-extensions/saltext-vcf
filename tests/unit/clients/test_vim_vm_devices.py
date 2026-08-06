"""Tests for clients.vim_vm_devices — USB controller functions (Broadcom KB 316384).

The tpm/vgpu/video/serial functions in this client have no existing test
coverage; these tests are scoped to only the USB-controller additions.
"""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_devices


def _usb2_controller(key=7000, label="USB Controller"):
    d = vim.vm.device.VirtualUSBController()
    d.key = key
    d.deviceInfo = vim.Description(label=label, summary=label)
    return d


def _usb3_controller(key=7001, label="USB xHCI Controller"):
    d = vim.vm.device.VirtualUSBXHCIController()
    d.key = key
    d.deviceInfo = vim.Description(label=label, summary=label)
    return d


def _scsi_controller(key=1000):
    d = vim.vm.device.VirtualSCSIController()
    d.key = key
    return d


def _fake_vm(devices, name="test-vm", moid="vm-100", connected=True):
    vm = MagicMock()
    vm._moId = moid
    vm.name = name
    vm.config.hardware.device = devices
    vm.runtime.connectionState = "connected" if connected else "disconnected"
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-1")
    return vm


@pytest.fixture
def vm_factory(monkeypatch):
    holder = {"vm": _fake_vm([])}

    def patcher(opts, vm_id, profile=None):
        return holder["vm"]

    monkeypatch.setattr(vim_vm_devices, "_vm", patcher)
    return holder


# ---------------------------------------------------------------------------
# single-VM: usb_controllers_list / usb_controllers_remove
# ---------------------------------------------------------------------------


def test_usb_controllers_list_empty(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    assert vim_vm_devices.usb_controllers_list(opts, "vm-100") == []


def test_usb_controllers_list_finds_both_types(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_usb2_controller(), _usb3_controller()])
    result = vim_vm_devices.usb_controllers_list(opts, "vm-100")
    assert len(result) == 2
    assert {r["label"] for r in result} == {"USB Controller", "USB xHCI Controller"}


def test_usb_controllers_list_ignores_other_device_types(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_scsi_controller()])
    assert vim_vm_devices.usb_controllers_list(opts, "vm-100") == []


def test_usb_controllers_remove_no_devices_is_noop(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    result = vim_vm_devices.usb_controllers_remove(opts, "vm-100")
    assert result == []
    vm_factory["vm"].ReconfigVM_Task.assert_not_called()


def test_usb_controllers_remove_batches_both_into_one_task(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_usb2_controller(), _usb3_controller()])
    result = vim_vm_devices.usb_controllers_remove(opts, "vm-100")
    assert len(result) == 2
    vm_factory["vm"].ReconfigVM_Task.assert_called_once()
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert len(spec.deviceChange) == 2
    assert all(change.operation == "remove" for change in spec.deviceChange)
    assert {type(change.device) for change in spec.deviceChange} == {
        vim.vm.device.VirtualUSBController,
        vim.vm.device.VirtualUSBXHCIController,
    }


def test_usb_controllers_remove_ignores_other_device_types(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_scsi_controller(), _usb2_controller()])
    result = vim_vm_devices.usb_controllers_remove(opts, "vm-100")
    assert len(result) == 1
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert len(spec.deviceChange) == 1
    assert isinstance(spec.deviceChange[0].device, vim.vm.device.VirtualUSBController)


# ---------------------------------------------------------------------------
# fleet-wide: list_vms_with_usb_controllers
# ---------------------------------------------------------------------------


def test_list_vms_with_usb_controllers_finds_matching_vms(opts, monkeypatch):
    vm_with_usb = _fake_vm([_usb2_controller()], name="vm-with-usb", moid="vm-1", connected=True)
    vm_without_usb = _fake_vm([], name="vm-without-usb", moid="vm-2", connected=True)
    vm_disconnected = _fake_vm(
        [_usb3_controller()], name="vm-disconnected", moid="vm-3", connected=False
    )

    container = MagicMock()
    container.view = [vm_with_usb, vm_without_usb, vm_disconnected]
    content = MagicMock()
    content.viewManager.CreateContainerView.return_value = container
    monkeypatch.setattr(vim_vm_devices.soap, "content", lambda opts, profile=None: content)

    result = vim_vm_devices.list_vms_with_usb_controllers(opts)

    assert {r["vm"] for r in result} == {"vm-with-usb", "vm-disconnected"}
    connected_flags = {r["vm"]: r["connected"] for r in result}
    assert connected_flags["vm-with-usb"] is True
    assert connected_flags["vm-disconnected"] is False
    moids = {r["vm"]: r["moid"] for r in result}
    assert moids["vm-with-usb"] == "vm-1"
    container.Destroy.assert_called_once()


def test_list_vms_with_usb_controllers_empty_inventory(opts, monkeypatch):
    container = MagicMock()
    container.view = []
    content = MagicMock()
    content.viewManager.CreateContainerView.return_value = container
    monkeypatch.setattr(vim_vm_devices.soap, "content", lambda opts, profile=None: content)

    assert vim_vm_devices.list_vms_with_usb_controllers(opts) == []


def test_list_vms_with_usb_controllers_skips_vms_without_config(opts, monkeypatch):
    vm_no_config = MagicMock()
    vm_no_config.config = None

    container = MagicMock()
    container.view = [vm_no_config]
    content = MagicMock()
    content.viewManager.CreateContainerView.return_value = container
    monkeypatch.setattr(vim_vm_devices.soap, "content", lambda opts, profile=None: content)

    assert vim_vm_devices.list_vms_with_usb_controllers(opts) == []
