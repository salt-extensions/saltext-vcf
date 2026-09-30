"""Tests for clients.vim_vm_boot (boot order/flags via SOAP)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_boot


def _fake_vm(**boot_kwargs):
    vm = MagicMock()
    boot = MagicMock(**boot_kwargs)
    boot.bootOrder = []
    vm.config.bootOptions = boot
    devices = []
    # A disk (key=2000), a cdrom (key=3000), an ethernet nic (key=4000), a floppy (key=16000)
    disk = MagicMock(spec=vim.vm.device.VirtualDisk)
    disk.key = 2000
    cdrom = MagicMock(spec=vim.vm.device.VirtualCdrom)
    cdrom.key = 3000
    nic = MagicMock(spec=vim.vm.device.VirtualEthernetCard)
    nic.key = 4000
    floppy = MagicMock(spec=vim.vm.device.VirtualFloppy)
    floppy.key = 16000
    devices = [disk, cdrom, nic, floppy]
    vm.config.hardware.device = devices
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-boot-1")
    return vm


def test_get_shape(opts):
    vm = _fake_vm()
    boot = vm.config.bootOptions
    boot.bootDelay = 5000
    boot.enterBIOSSetup = True
    boot.bootRetryEnabled = True
    boot.bootRetryDelay = 12000
    boot.efiSecureBootEnabled = True
    with patch.object(vim_vm_boot, "_vm", return_value=vm):
        result = vim_vm_boot.get(opts, "vm-1")
    assert result["delay"] == 5000
    assert result["enter_bios_setup"] is True
    assert result["retry_enabled"] is True
    assert result["retry_delay"] == 12000
    assert result["efi_secure_boot_enabled"] is True
    assert result["order"] == []


def test_set_builds_boot_order(opts):
    vm = _fake_vm()
    with patch.object(vim_vm_boot, "_vm", return_value=vm):
        moid = vim_vm_boot.set(
            opts,
            "vm-1",
            order=["cdrom", "disk", "ethernet", "floppy"],
            delay=5000,
            enter_bios_setup=True,
            retry_enabled=True,
            retry_delay=12000,
            efi_secure_boot=True,
        )
    assert moid == "task-boot-1"
    call = vm.ReconfigVM_Task.call_args
    spec = call.kwargs["spec"]
    order = spec.bootOptions.bootOrder
    assert isinstance(order[0], vim.vm.BootOptions.BootableCdromDevice)
    assert isinstance(order[1], vim.vm.BootOptions.BootableDiskDevice)
    assert order[1].deviceKey == 2000
    assert isinstance(order[2], vim.vm.BootOptions.BootableEthernetDevice)
    assert order[2].deviceKey == 4000
    assert isinstance(order[3], vim.vm.BootOptions.BootableFloppyDevice)
    assert spec.bootOptions.bootDelay == 5000
    assert spec.bootOptions.enterBIOSSetup is True
    assert spec.bootOptions.bootRetryEnabled is True
    assert spec.bootOptions.bootRetryDelay == 12000
    assert spec.bootOptions.efiSecureBootEnabled is True


def test_set_skips_missing_device_class(opts):
    vm = _fake_vm()
    # Remove the cdrom: order entry for it must be skipped silently.
    vm.config.hardware.device = [d for d in vm.config.hardware.device if not isinstance(d, MagicMock) or "Cdrom" in str(d)]
    # Simpler: keep only the disk.
    disk = MagicMock(spec=vim.vm.device.VirtualDisk)
    disk.key = 2000
    vm.config.hardware.device = [disk]
    with patch.object(vim_vm_boot, "_vm", return_value=vm):
        vim_vm_boot.set(opts, "vm-1", order=["cdrom", "disk"])
    spec = vm.ReconfigVM_Task.call_args.kwargs["spec"]
    order = spec.bootOptions.bootOrder
    assert len(order) == 1
    assert isinstance(order[0], vim.vm.BootOptions.BootableDiskDevice)


def test_set_rejects_invalid_order_name(opts):
    vm = _fake_vm()
    with patch.object(vim_vm_boot, "_vm", return_value=vm):
        with pytest.raises(ValueError):
            vim_vm_boot.set(opts, "vm-1", order=["tape"])


def test_compare_and_drift():
    current = {
        "order": ["cdrom", "disk"],
        "delay": 0,
        "enter_bios_setup": False,
        "retry_enabled": False,
        "retry_delay": 10000,
        "efi_secure_boot_enabled": False,
    }
    same = dict(current)
    assert vim_vm_boot.compare(same, current) is True
    assert vim_vm_boot.drift(same, current) == {}
    desired = dict(current, delay=5000)
    assert vim_vm_boot.compare(desired, current) is False
    assert vim_vm_boot.drift(desired, current) == {"delay": (0, 5000)}
