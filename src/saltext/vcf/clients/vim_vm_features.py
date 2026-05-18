"""VM advanced features + hardware version upgrade via SOAP.

Knobs covered:
 - Hot-add CPU/memory  (``cpuHotAddEnabled``, ``memoryHotAddEnabled``)
 - Nested hardware virtualization (``nestedHVEnabled``)
 - Latency sensitivity (``latencySensitivity.level``)
 - VMware Tools sync time with host (``tools.syncTimeWithHost``)
 - Boot options (firmware, ``bootDelay``, ``enterBIOSSetup``, ``efiSecureBootEnabled``)
 - Hardware version upgrade (``UpgradeVM_Task``)
"""

from pyVmomi import vim

from saltext.vcf.clients.vim_vm import _vm

_LATENCY_LEVELS = {"low", "normal", "medium", "high", "custom"}
_FIRMWARES = {"bios", "efi"}


def get_features(opts, vm_id_or_name, profile=None):
    """Return a snapshot of the feature toggles described above."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    cfg = vm.config
    boot = getattr(cfg, "bootOptions", None) or vim.vm.BootOptions()
    return {
        "cpuHotAddEnabled": cfg.cpuHotAddEnabled,
        "memoryHotAddEnabled": cfg.memoryHotAddEnabled,
        "nestedHVEnabled": cfg.nestedHVEnabled,
        "hardwareVersion": cfg.version,
        "latencySensitivity": str(cfg.latencySensitivity.level) if cfg.latencySensitivity else None,
        "toolsSyncTimeWithHost": cfg.tools.syncTimeWithHost if cfg.tools else None,
        "firmware": cfg.firmware,
        "bootDelay": getattr(boot, "bootDelay", None),
        "enterBIOSSetup": getattr(boot, "enterBIOSSetup", None),
        "efiSecureBootEnabled": getattr(boot, "efiSecureBootEnabled", None),
    }


def set_features(
    opts,
    vm_id_or_name,
    *,
    cpu_hot_add=None,
    memory_hot_add=None,
    nested_hv=None,
    latency_sensitivity=None,
    tools_sync_time_with_host=None,
    firmware=None,
    boot_delay=None,
    enter_bios_setup=None,
    efi_secure_boot=None,
    profile=None,
):
    """Update VM feature toggles via ReconfigVM_Task. Returns the task moid.

    Only non-None fields are touched; the rest are left as-is.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    config = vim.vm.ConfigSpec()

    if cpu_hot_add is not None:
        config.cpuHotAddEnabled = bool(cpu_hot_add)
    if memory_hot_add is not None:
        config.memoryHotAddEnabled = bool(memory_hot_add)
    if nested_hv is not None:
        config.nestedHVEnabled = bool(nested_hv)

    if latency_sensitivity is not None:
        if latency_sensitivity not in _LATENCY_LEVELS:
            raise ValueError(f"latency_sensitivity must be one of {sorted(_LATENCY_LEVELS)}")
        config.latencySensitivity = vim.LatencySensitivity(level=latency_sensitivity)

    if tools_sync_time_with_host is not None:
        config.tools = vim.vm.ToolsConfigInfo(syncTimeWithHost=bool(tools_sync_time_with_host))

    if firmware is not None:
        if firmware not in _FIRMWARES:
            raise ValueError(f"firmware must be one of {sorted(_FIRMWARES)}")
        config.firmware = firmware

    boot_changes = {}
    if boot_delay is not None:
        boot_changes["bootDelay"] = int(boot_delay)
    if enter_bios_setup is not None:
        boot_changes["enterBIOSSetup"] = bool(enter_bios_setup)
    if efi_secure_boot is not None:
        boot_changes["efiSecureBootEnabled"] = bool(efi_secure_boot)
    if boot_changes:
        config.bootOptions = vim.vm.BootOptions(**boot_changes)

    task = vm.ReconfigVM_Task(spec=config)
    return task._moId  # noqa: SLF001


def upgrade_hardware(opts, vm_id_or_name, version=None, profile=None):
    """Upgrade the VM hardware compatibility version. Returns the task moid.

    *version* is a string like ``"vmx-21"``. Pass ``None`` to upgrade to the
    host's latest supported version.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    kwargs = {"version": version} if version is not None else {}
    task = vm.UpgradeVM_Task(**kwargs)
    return task._moId  # noqa: SLF001
