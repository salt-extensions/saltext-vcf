"""Tests for clients.vim_vm_disk and clients.vim_vm_nic (SOAP, ReconfigVM_Task)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_disk
from saltext.vcf.clients import vim_vm_nic


def _scsi_controller(key=1000):
    c = vim.vm.device.VirtualSCSIController()
    c.key = key
    return c


def _disk(
    key,
    label,
    controller_key=1000,
    unit_number=0,
    capacity_kb=10485760,
    file_name="[ds] vm/disk.vmdk",
    disk_mode="persistent",
):
    d = vim.vm.device.VirtualDisk()
    d.key = key
    d.deviceInfo = vim.Description(label=label, summary=f"{capacity_kb // 1024} MB")
    d.controllerKey = controller_key
    d.unitNumber = unit_number
    d.capacityInKB = capacity_kb
    backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
    backing.fileName = file_name
    backing.diskMode = disk_mode
    backing.thinProvisioned = True
    backing.eagerlyScrub = False
    d.backing = backing
    return d


def _nic(
    key,
    label,
    network_moid=None,
    portgroup_key=None,
    dvs_uuid=None,
    mac="00:50:56:00:00:01",
    connected=True,
    nic_cls=vim.vm.device.VirtualVmxnet3,
):
    n = nic_cls()
    n.key = key
    n.deviceInfo = vim.Description(label=label, summary=label)
    n.macAddress = mac
    n.addressType = "assigned"
    if portgroup_key:
        backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        backing.port = vim.dvs.PortConnection(portgroupKey=portgroup_key, switchUuid=dvs_uuid)
    else:
        backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        if network_moid:
            backing.network = vim.Network(network_moid, None)
            backing.deviceName = ""
    n.backing = backing
    conn = vim.vm.device.VirtualDevice.ConnectInfo()
    conn.connected = connected
    conn.startConnected = connected
    conn.allowGuestControl = True
    n.connectable = conn
    return n


def _fake_vm(devices, name="test-vm", moid="vm-100"):
    vm = MagicMock()
    vm._moId = moid
    vm.name = name
    vm.config.hardware.device = devices
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-1")
    return vm


@pytest.fixture
def vm_factory(monkeypatch):
    holder = {"vm": _fake_vm([])}

    def patcher(opts, vm_id, profile=None):
        return holder["vm"]

    monkeypatch.setattr(vim_vm_disk, "_vm", patcher)
    monkeypatch.setattr(vim_vm_nic, "_vm", patcher)
    return holder


# ---------- disks ----------


def test_disk_list_returns_records(vm_factory, opts):
    vm_factory["vm"] = _fake_vm(
        [_scsi_controller(), _disk(2000, "Hard disk 1", capacity_kb=10 * 1024 * 1024)]
    )
    result = vim_vm_disk.list_(opts, "vm-100")
    assert len(result) == 1
    assert result[0]["key"] == 2000
    assert result[0]["capacity_kb"] == 10 * 1024 * 1024


def test_disk_add_creates_spec(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_scsi_controller(key=1000)])
    vim_vm_disk.add(opts, "vm-100", size_gb=20)
    spec = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert len(spec.deviceChange) == 1
    change = spec.deviceChange[0]
    assert change.operation == "add"
    assert change.fileOperation == "create"
    assert isinstance(change.device, vim.vm.device.VirtualDisk)
    assert change.device.capacityInKB == 20 * 1024 * 1024
    assert change.device.controllerKey == 1000


def test_disk_add_picks_next_unit_number_skipping_7(vm_factory, opts):
    vm_factory["vm"] = _fake_vm(
        [
            _scsi_controller(),
            _disk(2000, "d1", unit_number=0),
            _disk(2001, "d2", unit_number=1),
        ]
    )
    vim_vm_disk.add(opts, "vm-100", size_gb=10)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.device.unitNumber == 2


def test_disk_resize(vm_factory, opts):
    vm_factory["vm"] = _fake_vm(
        [_scsi_controller(), _disk(2000, "d1", capacity_kb=10 * 1024 * 1024)]
    )
    vim_vm_disk.resize(opts, "vm-100", 2000, size_gb=20)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "edit"
    assert change.device.capacityInKB == 20 * 1024 * 1024


def test_disk_remove_default_keeps_files(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_scsi_controller(), _disk(2000, "d1")])
    vim_vm_disk.remove(opts, "vm-100", 2000)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "remove"
    assert change.fileOperation is None or change.fileOperation == ""


def test_disk_remove_destroys_files(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_scsi_controller(), _disk(2000, "d1")])
    vim_vm_disk.remove(opts, "vm-100", 2000, destroy_files=True)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.fileOperation == "destroy"


def test_disk_remove_missing_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_scsi_controller()])
    with pytest.raises(LookupError):
        vim_vm_disk.remove(opts, "vm-100", 999)


def test_disk_add_no_controller_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    with pytest.raises(LookupError, match="SCSI"):
        vim_vm_disk.add(opts, "vm-100", size_gb=10)


# ---------- NICs ----------


def test_nic_list_legacy_network(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_nic(4000, "Network adapter 1", network_moid="network-12")])
    result = vim_vm_nic.list_(opts, "vm-100")
    assert len(result) == 1
    assert result[0]["key"] == 4000
    assert result[0]["network_moid"] == "network-12"
    assert result[0]["device_type"] == "vim.vm.device.VirtualVmxnet3"


def test_nic_list_distributed(vm_factory, opts):
    vm_factory["vm"] = _fake_vm(
        [_nic(4000, "n1", portgroup_key="dvportgroup-25", dvs_uuid="50 2f ...")]
    )
    result = vim_vm_nic.list_(opts, "vm-100")
    assert result[0]["portgroup_key"] == "dvportgroup-25"


def test_nic_add_legacy_network(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    vim_vm_nic.add(opts, "vm-100", network_moid="network-12")
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "add"
    assert isinstance(change.device, vim.vm.device.VirtualVmxnet3)
    assert isinstance(change.device.backing, vim.vm.device.VirtualEthernetCard.NetworkBackingInfo)


def test_nic_add_distributed(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    vim_vm_nic.add(
        opts,
        "vm-100",
        portgroup_key="dvportgroup-25",
        dvs_uuid="50 2f ...",
    )
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert isinstance(
        change.device.backing,
        vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo,
    )
    assert change.device.backing.port.portgroupKey == "dvportgroup-25"


def test_nic_add_manual_mac(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    vim_vm_nic.add(opts, "vm-100", network_moid="network-12", mac_address="00:50:56:99:99:99")
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.device.macAddress == "00:50:56:99:99:99"
    assert change.device.addressType == "manual"


def test_nic_add_unknown_type_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    with pytest.raises(ValueError, match="unknown nic_type"):
        vim_vm_nic.add(opts, "vm-100", nic_type="bogus", network_moid="network-12")


def test_nic_add_no_backing_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    with pytest.raises(ValueError, match="network_moid OR"):
        vim_vm_nic.add(opts, "vm-100")


def test_nic_update_backing_to_dvportgroup(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_nic(4000, "n1", network_moid="network-12")])
    vim_vm_nic.update_backing(opts, "vm-100", 4000, portgroup_key="dvportgroup-25", dvs_uuid="x")
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "edit"
    assert change.device.backing.port.portgroupKey == "dvportgroup-25"


def test_nic_set_connected_false(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_nic(4000, "n1", network_moid="network-12")])
    vim_vm_nic.set_connected(opts, "vm-100", 4000, False)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.device.connectable.connected is False
    assert change.device.connectable.startConnected is False


def test_nic_remove(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([_nic(4000, "n1", network_moid="network-12")])
    vim_vm_nic.remove(opts, "vm-100", 4000)
    change = vm_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"].deviceChange[0]
    assert change.operation == "remove"


def test_nic_remove_missing_raises(vm_factory, opts):
    vm_factory["vm"] = _fake_vm([])
    with pytest.raises(LookupError):
        vim_vm_nic.remove(opts, "vm-100", 999)
