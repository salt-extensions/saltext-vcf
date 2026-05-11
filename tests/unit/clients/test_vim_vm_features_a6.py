"""Tests for clients.vim_vm_features (A6)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_vm_features


def _fake_vm(**overrides):
    vm = MagicMock()
    vm._moId = "vm-100"
    cfg = vm.config
    cfg.cpuHotAddEnabled = overrides.get("cpu_hot_add", False)
    cfg.memoryHotAddEnabled = overrides.get("mem_hot_add", False)
    cfg.nestedHVEnabled = overrides.get("nested_hv", False)
    cfg.version = overrides.get("version", "vmx-20")
    cfg.latencySensitivity = vim.LatencySensitivity(level="normal")
    cfg.tools = vim.vm.ToolsConfigInfo(syncTimeWithHost=overrides.get("sync_time", False))
    cfg.firmware = overrides.get("firmware", "efi")
    cfg.bootOptions = vim.vm.BootOptions(
        bootDelay=overrides.get("boot_delay", 0),
        enterBIOSSetup=overrides.get("enter_bios", False),
        efiSecureBootEnabled=overrides.get("secure_boot", True),
    )
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-cfg")
    vm.UpgradeVM_Task.return_value = MagicMock(_moId="task-upg")
    return vm


@pytest.fixture
def factory(monkeypatch):
    holder = {"vm": _fake_vm()}
    monkeypatch.setattr(vim_vm_features, "_vm", lambda opts, vid, profile=None: holder["vm"])
    return holder


def test_get_features_snapshot(factory, opts):
    out = vim_vm_features.get_features(opts, "vm-100")
    assert out["cpuHotAddEnabled"] is False
    assert out["nestedHVEnabled"] is False
    assert out["hardwareVersion"] == "vmx-20"
    assert out["firmware"] == "efi"
    assert out["latencySensitivity"] == "normal"
    assert out["efiSecureBootEnabled"] is True


def test_set_features_toggles(factory, opts):
    vim_vm_features.set_features(
        opts,
        "vm-100",
        cpu_hot_add=True,
        memory_hot_add=True,
        nested_hv=True,
        tools_sync_time_with_host=True,
    )
    spec = factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.cpuHotAddEnabled is True
    assert spec.memoryHotAddEnabled is True
    assert spec.nestedHVEnabled is True
    assert spec.tools.syncTimeWithHost is True


def test_set_latency_sensitivity_maps_enum(factory, opts):
    vim_vm_features.set_features(opts, "vm-100", latency_sensitivity="high")
    spec = factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.latencySensitivity.level == "high"


def test_set_invalid_latency_raises(factory, opts):
    with pytest.raises(ValueError):
        vim_vm_features.set_features(opts, "vm-100", latency_sensitivity="extreme")


def test_set_firmware_validation(factory, opts):
    vim_vm_features.set_features(opts, "vm-100", firmware="bios")
    spec = factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.firmware == "bios"
    with pytest.raises(ValueError):
        vim_vm_features.set_features(opts, "vm-100", firmware="coreboot")


def test_set_boot_options(factory, opts):
    vim_vm_features.set_features(
        opts, "vm-100", boot_delay=5000, enter_bios_setup=True, efi_secure_boot=False
    )
    spec = factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.bootOptions.bootDelay == 5000
    assert spec.bootOptions.enterBIOSSetup is True
    assert spec.bootOptions.efiSecureBootEnabled is False


def test_set_features_no_args_still_calls_reconfig(factory, opts):
    """With nothing to change, we still issue an empty ReconfigVM_Task (no-op)."""
    out = vim_vm_features.set_features(opts, "vm-100")
    assert out == "task-cfg"


def test_upgrade_hardware_no_version(factory, opts):
    assert vim_vm_features.upgrade_hardware(opts, "vm-100") == "task-upg"
    factory["vm"].UpgradeVM_Task.assert_called_once_with()


def test_upgrade_hardware_explicit_version(factory, opts):
    vim_vm_features.upgrade_hardware(opts, "vm-100", version="vmx-21")
    factory["vm"].UpgradeVM_Task.assert_called_once_with(version="vmx-21")


def test_module_wrappers_delegate(factory, opts, monkeypatch):
    from saltext.vmware.modules import vmware_vim_vm_features as m

    monkeypatch.setattr(m, "__opts__", opts, raising=False)
    assert m.get_features("vm-100")["hardwareVersion"] == "vmx-20"
    assert m.upgrade_hardware("vm-100") == "task-upg"
