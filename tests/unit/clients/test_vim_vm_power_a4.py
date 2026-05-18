"""Tests for clients.vim_vm_power and clients.vim_vm_tools (A4)."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import vim_vm_power
from saltext.vcf.clients import vim_vm_tools


def _fake_vm(power_state="poweredOn", name="test-vm", moid="vm-100"):
    vm = MagicMock()
    vm._moId = moid
    vm.name = name
    vm.runtime.powerState = power_state
    vm.PowerOnVM_Task.return_value = MagicMock(_moId="task-on")
    vm.PowerOffVM_Task.return_value = MagicMock(_moId="task-off")
    vm.ResetVM_Task.return_value = MagicMock(_moId="task-reset")
    vm.SuspendVM_Task.return_value = MagicMock(_moId="task-suspend")
    vm.UpgradeTools_Task.return_value = MagicMock(_moId="task-tools")
    vm.guest.toolsStatus = "toolsOk"
    vm.guest.toolsVersionStatus2 = "guestToolsCurrent"
    vm.guest.toolsRunningStatus = "guestToolsRunning"
    vm.guest.toolsInstallType = "guestToolsTypeMSI"
    vm.guest.toolsVersion = "12345"
    return vm


@pytest.fixture
def vm_factory(monkeypatch):
    holder = {"vm": _fake_vm()}

    def patcher(opts, vm_id, profile=None):
        return holder["vm"]

    monkeypatch.setattr(vim_vm_power, "_vm", patcher)
    monkeypatch.setattr(vim_vm_tools, "_vm", patcher)
    return holder


# -- power lifecycle ------------------------------------------------------


def test_get_power_state(vm_factory, opts):
    assert vim_vm_power.get_power_state(opts, "vm-100") == "poweredOn"


def test_power_on(vm_factory, opts):
    assert vim_vm_power.power_on(opts, "vm-100") == "task-on"
    vm_factory["vm"].PowerOnVM_Task.assert_called_once_with(host=None)


def test_power_on_with_host(vm_factory, opts, monkeypatch):
    host_obj = MagicMock(_moId="host-7")
    monkeypatch.setattr(
        vim_vm_power,
        "_find_by_type",
        lambda opts, t, name, profile=None: host_obj,
    )
    vim_vm_power.power_on(opts, "vm-100", host="host-7")
    vm_factory["vm"].PowerOnVM_Task.assert_called_once_with(host=host_obj)


def test_power_off(vm_factory, opts):
    assert vim_vm_power.power_off(opts, "vm-100") == "task-off"
    vm_factory["vm"].PowerOffVM_Task.assert_called_once()


def test_shutdown_guest(vm_factory, opts):
    assert vim_vm_power.shutdown_guest(opts, "vm-100") is True
    vm_factory["vm"].ShutdownGuest.assert_called_once()


def test_reboot_guest(vm_factory, opts):
    assert vim_vm_power.reboot_guest(opts, "vm-100") is True
    vm_factory["vm"].RebootGuest.assert_called_once()


def test_standby_guest(vm_factory, opts):
    assert vim_vm_power.standby_guest(opts, "vm-100") is True
    vm_factory["vm"].StandbyGuest.assert_called_once()


def test_reset(vm_factory, opts):
    assert vim_vm_power.reset(opts, "vm-100") == "task-reset"
    vm_factory["vm"].ResetVM_Task.assert_called_once()


def test_suspend(vm_factory, opts):
    assert vim_vm_power.suspend(opts, "vm-100") == "task-suspend"
    vm_factory["vm"].SuspendVM_Task.assert_called_once()


# -- tools ----------------------------------------------------------------


def test_get_tools_status(vm_factory, opts):
    out = vim_vm_tools.get_tools_status(opts, "vm-100")
    assert out["toolsStatus"] == "toolsOk"
    assert out["toolsRunningStatus"] == "guestToolsRunning"
    assert out["toolsVersion"] == "12345"


def test_upgrade_tools_passes_options(vm_factory, opts):
    out = vim_vm_tools.upgrade_tools(opts, "vm-100", installer_options="--silent")
    assert out == "task-tools"
    vm_factory["vm"].UpgradeTools_Task.assert_called_once_with(installerOptions="--silent")


def test_mount_unmount_tools_installer(vm_factory, opts):
    assert vim_vm_tools.mount_tools_installer(opts, "vm-100") is True
    vm_factory["vm"].MountToolsInstaller.assert_called_once()
    assert vim_vm_tools.unmount_tools_installer(opts, "vm-100") is True
    vm_factory["vm"].UnmountToolsInstaller.assert_called_once()


def test_module_wrappers_delegate(vm_factory, opts, monkeypatch):
    from saltext.vcf.modules import vcf_vim_vm_power as m

    monkeypatch.setattr(m, "__opts__", opts, raising=False)
    assert m.get_power_state("vm-100") == "poweredOn"
    assert m.power_off("vm-100") == "task-off"
    assert m.get_tools_status("vm-100")["toolsStatus"] == "toolsOk"
