"""Tests for clients.vim_vm_cdrom (SOAP, ReconfigVM_Task)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_cdrom


def _ide_controller(key=200, device_keys=()):
    ctrl = vim.vm.device.VirtualIDEController()
    ctrl.key = key
    ctrl.device = list(device_keys)
    return ctrl


def _cdrom(key, label="CD/DVD drive 1", controller_key=200, iso_path=None):
    d = vim.vm.device.VirtualCdrom()
    d.key = key
    d.deviceInfo = vim.Description(label=label, summary=label)
    d.controllerKey = controller_key
    d.unitNumber = 0
    if iso_path:
        d.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)
    else:
        d.backing = vim.vm.device.VirtualCdrom.AtapiBackingInfo(deviceName="")
    conn = vim.vm.device.VirtualDevice.ConnectInfo()
    conn.startConnected = bool(iso_path)
    conn.connected = bool(iso_path)
    conn.allowGuestControl = True
    d.connectable = conn
    return d


def _fake_vm(devices, name="test-vm", moid="vm-100"):
    vm = MagicMock()
    vm._moId = moid
    vm.name = name
    vm.config.hardware.device = devices
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-1")
    return vm


def _fake_datastore(name="datastore-ssd-4tb", moid="datastore-5"):
    ds = MagicMock()
    ds.name = name
    ds._moId = moid
    return ds


@pytest.fixture
def vm_factory(monkeypatch):
    holder = {"vm": _fake_vm([])}

    def patcher(opts, vm_id, profile=None):
        return holder["vm"]

    monkeypatch.setattr(vim_vm_cdrom, "_vm", patcher)
    return holder


@pytest.fixture
def datastore_factory(monkeypatch):
    holder = {"ds": _fake_datastore()}

    def patcher(opts, name_or_id, profile=None):
        return holder["ds"]

    monkeypatch.setattr(vim_vm_cdrom, "_find_datastore", patcher)
    return holder


def test_list_returns_records(vm_factory, opts):
    vm_factory["vm"] = _fake_vm(
        [_ide_controller(), _cdrom(3000, iso_path="[ds] isos/foo.iso")]
    )
    result = vim_vm_cdrom.list_(opts, "vm-100")
    assert len(result) == 1
    assert result[0]["key"] == 3000
    assert result[0]["iso_path"] == "[ds] isos/foo.iso"
    assert result[0]["connected"] is True


def test_add_empty_cdrom_uses_atapi_backing(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller(key=200)])
    vim_vm_cdrom.add(opts, "vm-100")
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    change = spec.deviceChange[0]
    assert change.operation == "add"
    assert isinstance(change.device, vim.vm.device.VirtualCdrom)
    assert isinstance(change.device.backing, vim.vm.device.VirtualCdrom.AtapiBackingInfo)
    assert change.device.controllerKey == 200


def test_add_with_absolute_iso_path(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller()])
    vim_vm_cdrom.add(opts, "vm-100", iso_path="[datastore-ssd-4tb] isos/foo.iso")
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert isinstance(change.device.backing, vim.vm.device.VirtualCdrom.IsoBackingInfo)
    assert change.device.backing.fileName == "[datastore-ssd-4tb] isos/foo.iso"


def test_add_relative_iso_path_needs_datastore(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller()])
    with pytest.raises(ValueError, match="datastore"):
        vim_vm_cdrom.add(opts, "vm-100", iso_path="isos/foo.iso")


def test_add_relative_iso_path_resolves(vm_factory, datastore_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller()])
    vim_vm_cdrom.add(
        opts, "vm-100", iso_path="isos/foo.iso", datastore="datastore-ssd-4tb"
    )
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.device.backing.fileName == "[datastore-ssd-4tb] isos/foo.iso"


def test_add_no_ide_controller_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    with pytest.raises(LookupError, match="IDE"):
        vim_vm_cdrom.add(opts, "vm-100")


def test_add_all_ide_slots_full_raises(vm_factory, opts):
    # Both controllers each carrying two devices → no room.
    vm_factory["vm"] = _fake_vm(
        [
            _ide_controller(key=200, device_keys=(3000, 3001)),
            _ide_controller(key=201, device_keys=(3002, 3003)),
        ]
    )
    with pytest.raises(ValueError, match="full"):
        vim_vm_cdrom.add(opts, "vm-100")


def test_attach_iso_edits_existing_cdrom(vm_factory, datastore_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller(), _cdrom(3000)])
    vim_vm_cdrom.attach_iso(
        opts, "vm-100", "isos/bar.iso", datastore="datastore-ssd-4tb"
    )
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "edit"
    assert isinstance(change.device.backing, vim.vm.device.VirtualCdrom.IsoBackingInfo)
    assert change.device.backing.fileName == "[datastore-ssd-4tb] isos/bar.iso"
    assert change.device.connectable.connected is True


def test_attach_iso_absolute_path_skips_datastore_lookup(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller(), _cdrom(3000)])
    vim_vm_cdrom.attach_iso(opts, "vm-100", "[ds] path.iso")
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.device.backing.fileName == "[ds] path.iso"


def test_attach_iso_no_cdrom_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller()])
    with pytest.raises(LookupError, match="CD-ROM"):
        vim_vm_cdrom.attach_iso(opts, "vm-100", "[ds] path.iso")


def test_eject_replaces_backing_with_atapi(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller(), _cdrom(3000, iso_path="[ds] a.iso")])
    vim_vm_cdrom.eject(opts, "vm-100")
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert isinstance(change.device.backing, vim.vm.device.VirtualCdrom.AtapiBackingInfo)
    assert change.device.connectable.connected is False


def test_remove(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller(), _cdrom(3000)])
    vim_vm_cdrom.remove(opts, "vm-100", 3000)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "remove"


def test_remove_missing_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_ide_controller()])
    with pytest.raises(LookupError):
        vim_vm_cdrom.remove(opts, "vm-100", 999)
