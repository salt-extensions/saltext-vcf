"""VM boot options (boot order, delay, BIOS setup, boot retry, secure boot).

Port of ``vmware_vm.set_boot_manager`` from ``saltext.vmware``. The
boot order is expressed as a list of friendly device-class names —
``cdrom``, ``disk``, ``ethernet``, ``floppy`` — and mapped onto
``vim.vm.BootOptions.Bootable*Device`` objects resolved from the VM's
current hardware inventory.

Implemented via ``VirtualMachine.ReconfigVM_Task`` with a
``vim.vm.BootOptions`` spec.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap

from saltext.vcf.clients.vim_vm import _vm  # noqa: PLC0415  (re-export for state layer)

_BOOTABLE_CLASSES = {
    "cdrom": vim.vm.BootOptions.BootableCdromDevice,
    "disk": vim.vm.BootOptions.BootableDiskDevice,
    "ethernet": vim.vm.BootOptions.BootableEthernetDevice,
    "floppy": vim.vm.BootOptions.BootableFloppyDevice,
}

_BOOTABLE_TO_NAME = {cls: name for name, cls in _BOOTABLE_CLASSES.items()}


def _device_key(vm, device_name):
    """Resolve the first hardware device of *device_name* on *vm* to its key."""
    needle = {
        "cdrom": vim.vm.device.VirtualCdrom,
        "disk": vim.vm.device.VirtualDisk,
        "ethernet": vim.vm.device.VirtualEthernetCard,
        "floppy": vim.vm.device.VirtualFloppy,
    }[device_name]
    for dev in vm.config.hardware.device or []:
        if isinstance(dev, needle):
            return dev.key
    return None


def _order_devices(vm, order):
    """Build the ``bootOrder`` list for *order* (list of device-class names).

    Skips device classes the VM has no matching hardware for (mirrors
    ``vmware_vm.options_order_list`` which would raise instead — we are
    more lenient so re-apply of an existing order never breaks).
    """
    out = []
    for name in order or []:
        if name not in _BOOTABLE_CLASSES:
            raise ValueError(f"invalid boot device {name!r}; valid: {sorted(_BOOTABLE_CLASSES)}")
        key = _device_key(vm, name)
        if key is None:
            continue
        cls = _BOOTABLE_CLASSES[name]
        if cls is vim.vm.BootOptions.BootableDiskDevice:
            out.append(cls(deviceKey=key))
        elif cls is vim.vm.BootOptions.BootableEthernetDevice:
            out.append(cls(deviceKey=key))
        else:
            out.append(cls())
    return out


def _order_names(current):
    """Convert a current ``bootOrder`` list back to friendly names."""
    names = []
    for dev in current or []:
        name = _BOOTABLE_TO_NAME.get(type(dev))
        names.append(name if name is not None else str(type(dev).__name__))
    return names


def get(opts, vm_id_or_name, profile=None):
    """Return the VM's boot options as a dict.

    Shape::

        {
            "order": ["cdrom", "disk", ...],
            "delay": <int>,              # ms
            "enter_bios_setup": <bool>,
            "retry_enabled": <bool>,
            "retry_delay": <int>,        # ms
            "efi_secure_boot_enabled": <bool>,
        }
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    boot = vm.config.bootOptions or vim.vm.BootOptions()
    return {
        "order": _order_names(getattr(boot, "bootOrder", None)),
        "delay": getattr(boot, "bootDelay", 0),
        "enter_bios_setup": bool(getattr(boot, "enterBIOSSetup", False)),
        "retry_enabled": bool(getattr(boot, "bootRetryEnabled", False)),
        "retry_delay": getattr(boot, "bootRetryDelay", 10000),
        "efi_secure_boot_enabled": bool(getattr(boot, "efiSecureBootEnabled", False)),
    }


def set(
    opts,
    vm_id_or_name,
    *,
    order=None,
    delay=None,
    enter_bios_setup=None,
    retry_enabled=None,
    retry_delay=None,
    efi_secure_boot=None,
    profile=None,
):
    """Update VM boot options via ``ReconfigVM_Task``. Returns task moid.

    *order* is a list of device-class names (``cdrom``, ``disk``,
    ``ethernet``, ``floppy``); entries without matching hardware are
    skipped. Only non-None fields are applied.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    boot_kwargs = {}
    if order is not None:
        boot_kwargs["bootOrder"] = _order_devices(vm, order)
    if delay is not None:
        boot_kwargs["bootDelay"] = int(delay)
    if enter_bios_setup is not None:
        boot_kwargs["enterBIOSSetup"] = bool(enter_bios_setup)
    if retry_enabled is not None:
        boot_kwargs["bootRetryEnabled"] = bool(retry_enabled)
    if retry_delay is not None:
        boot_kwargs["bootRetryDelay"] = int(retry_delay)
    if efi_secure_boot is not None:
        boot_kwargs["efiSecureBootEnabled"] = bool(efi_secure_boot)
    config = vim.vm.ConfigSpec(bootOptions=vim.vm.BootOptions(**boot_kwargs))
    task = vm.ReconfigVM_Task(spec=config)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def compare(desired, current):
    """Return ``True`` when *desired* (get-shape dict) equals *current* (get-shape dict)."""
    return desired == current


def drift(desired, current):
    """Return a ``{field: (old, new)}`` dict of differences between the two get-shape dicts."""
    ret = {}
    for field in ("order", "delay", "enter_bios_setup", "retry_enabled", "retry_delay",
                  "efi_secure_boot_enabled"):
        if desired.get(field) != current.get(field):
            ret[field] = (current.get(field), desired.get(field))
    return ret
