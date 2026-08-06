"""Niche VM virtual-device CRUD: vTPM, vGPU, serial port, video card, USB controllers.

Uses the same device-spec idiom as :mod:`vim_vm_disk` and :mod:`vim_vm_nic`:
build a ``vim.vm.device.Virtual*`` device, wrap in a
``VirtualDeviceConfigSpec`` with ``operation="add|remove|edit"``, and call
``vm.ReconfigVM_Task``.
"""

from pyVmomi import vim

from saltext.vcf.clients.vim_vm import _vm
from saltext.vcf.utils import vim as soap


def _reconfig(vm, device_spec):
    spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
    task = vm.ReconfigVM_Task(spec=spec)
    return task._moId  # noqa: SLF001


def _devices(vm, dev_type):
    return [d for d in vm.config.hardware.device if isinstance(d, dev_type)]


def _device_summary(d):
    base = {
        "key": int(d.key),
        "label": d.deviceInfo.label if d.deviceInfo else None,
        "summary": d.deviceInfo.summary if d.deviceInfo else None,
    }
    return base


# ---------------------------------------------------------------------------
# vTPM
# ---------------------------------------------------------------------------


def tpm_list(opts, vm_id_or_name, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    return [_device_summary(d) for d in _devices(vm, vim.vm.device.VirtualTPM)]


def tpm_add(opts, vm_id_or_name, profile=None):
    """Attach a vTPM 2.0 device. VM must be powered off."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    tpm = vim.vm.device.VirtualTPM(key=-1)
    return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="add", device=tpm))


def tpm_remove(opts, vm_id_or_name, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    existing = _devices(vm, vim.vm.device.VirtualTPM)
    if not existing:
        raise LookupError(f"VM {vm_id_or_name!r} has no vTPM device")
    return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="remove", device=existing[0]))


# ---------------------------------------------------------------------------
# vGPU (PCI passthrough with vGPU backing)
# ---------------------------------------------------------------------------


def vgpu_list(opts, vm_id_or_name, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    out = []
    for d in _devices(vm, vim.vm.device.VirtualPCIPassthrough):
        backing = d.backing
        profile_name = (
            backing.vgpu
            if isinstance(backing, vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo)
            else None
        )
        info = _device_summary(d)
        info["vgpu_profile"] = profile_name
        out.append(info)
    return out


def vgpu_add(opts, vm_id_or_name, profile_name, profile=None):
    """Attach a vGPU (NVIDIA vGRID) device. Requires host with vGPU-capable card.

    *profile_name* — vGPU profile string, e.g. ``grid_a100d-8c``.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    backing = vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo(vgpu=profile_name)
    dev = vim.vm.device.VirtualPCIPassthrough(key=-1, backing=backing)
    return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="add", device=dev))


def vgpu_remove(opts, vm_id_or_name, profile_name=None, profile=None):
    """Detach a vGPU. If *profile_name* given, only remove that profile."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    for d in _devices(vm, vim.vm.device.VirtualPCIPassthrough):
        backing = d.backing
        if not isinstance(backing, vim.vm.device.VirtualPCIPassthrough.VmiopBackingInfo):
            continue
        if profile_name is None or backing.vgpu == profile_name:
            return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="remove", device=d))
    raise LookupError(f"no matching vGPU device on VM {vm_id_or_name!r}")


# ---------------------------------------------------------------------------
# Video card
# ---------------------------------------------------------------------------


def video_get(opts, vm_id_or_name, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    cards = _devices(vm, vim.vm.device.VirtualVideoCard)
    if not cards:
        return None
    card = cards[0]
    return {
        "key": int(card.key),
        "video_ram_size_kb": int(card.videoRamSizeInKB or 0),
        "num_displays": int(card.numDisplays or 1),
        "use_auto_detect": bool(card.useAutoDetect),
        "enable_3d_support": bool(card.enable3DSupport),
        "graphics_memory_size_kb": int(getattr(card, "graphicsMemorySizeInKB", 0) or 0),
    }


def video_update(
    opts,
    vm_id_or_name,
    *,
    video_ram_size_kb=None,
    num_displays=None,
    enable_3d_support=None,
    graphics_memory_size_kb=None,
    profile=None,
):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    cards = _devices(vm, vim.vm.device.VirtualVideoCard)
    if not cards:
        raise LookupError(f"VM {vm_id_or_name!r} has no video card")
    card = cards[0]
    if video_ram_size_kb is not None:
        card.videoRamSizeInKB = int(video_ram_size_kb)
    if num_displays is not None:
        card.numDisplays = int(num_displays)
    if enable_3d_support is not None:
        card.enable3DSupport = bool(enable_3d_support)
    if graphics_memory_size_kb is not None:
        card.graphicsMemorySizeInKB = int(graphics_memory_size_kb)
    return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="edit", device=card))


# ---------------------------------------------------------------------------
# Serial port
# ---------------------------------------------------------------------------


def serial_list(opts, vm_id_or_name, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    out = []
    for d in _devices(vm, vim.vm.device.VirtualSerialPort):
        backing = d.backing
        info = _device_summary(d)
        info["backing_type"] = type(backing).__name__ if backing else None
        if isinstance(backing, vim.vm.device.VirtualSerialPort.URIBackingInfo):
            info["uri"] = backing.serviceURI
            info["direction"] = backing.direction
        elif isinstance(backing, vim.vm.device.VirtualSerialPort.FileBackingInfo):
            info["file"] = backing.fileName
        out.append(info)
    return out


def serial_add(
    opts,
    vm_id_or_name,
    *,
    backing="network",
    uri=None,
    direction="server",
    file_path=None,
    profile=None,
):
    """Add a serial port.

    *backing* — ``"network"`` (URI) or ``"file"``. For ``"network"``, supply
    *uri* (e.g. ``tcp://0.0.0.0:9000``) and *direction* (``server``/``client``).
    For ``"file"``, supply *file_path* (e.g. ``[ds1] vm/serial.log``).
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    if backing == "network":
        if not uri:
            raise ValueError("uri is required when backing='network'")
        be = vim.vm.device.VirtualSerialPort.URIBackingInfo(serviceURI=uri, direction=direction)
    elif backing == "file":
        if not file_path:
            raise ValueError("file_path is required when backing='file'")
        be = vim.vm.device.VirtualSerialPort.FileBackingInfo(fileName=file_path)
    else:
        raise ValueError(f"unsupported backing: {backing!r}")
    port = vim.vm.device.VirtualSerialPort(key=-1, backing=be, yieldOnPoll=True)
    return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="add", device=port))


def serial_remove(opts, vm_id_or_name, key=None, profile=None):
    """Remove a serial port. If *key* is None, removes the first one."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    for d in _devices(vm, vim.vm.device.VirtualSerialPort):
        if key is None or int(d.key) == int(key):
            return _reconfig(vm, vim.vm.device.VirtualDeviceSpec(operation="remove", device=d))
    raise LookupError(f"no matching serial port on VM {vm_id_or_name!r}")


# ---------------------------------------------------------------------------
# USB controllers (Broadcom KB 316384: unauthorized USB peripheral passthrough)
# ---------------------------------------------------------------------------

# Covers both the USB 2.0 controller (EHCI+UHCI) and the USB 3.x xHCI
# controller — a VM can have either or both. Matched by device type rather
# than the KB's reference PowerCLI script's ``DeviceInfo.Label -match
# "USB"`` string match, which is more fragile (UI label text, not a
# stable API contract).
_USB_CONTROLLER_TYPES = (
    vim.vm.device.VirtualUSBController,
    vim.vm.device.VirtualUSBXHCIController,
)


def usb_controllers_list(opts, vm_id_or_name, profile=None):
    """List USB controller devices (USB 2.0 and/or USB 3.x xHCI) on *vm*."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    return [_device_summary(d) for d in _devices(vm, _USB_CONTROLLER_TYPES)]


def usb_controllers_remove(opts, vm_id_or_name, profile=None):
    """Remove every USB controller device from *vm*. Returns the removed device summaries.

    Batches all removals into one ``ReconfigVM_Task`` call — the KB's
    reference PowerCLI script issues a separate task per device with a
    sleep in between, but a VM has at most one USB 2.0 and one USB 3.x
    controller, so batching is both faster and atomic.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    targets = _devices(vm, _USB_CONTROLLER_TYPES)
    if not targets:
        return []
    spec = vim.vm.ConfigSpec(
        deviceChange=[
            vim.vm.device.VirtualDeviceSpec(operation="remove", device=d) for d in targets
        ]
    )
    vm.ReconfigVM_Task(spec=spec)
    return [_device_summary(d) for d in targets]


def list_vms_with_usb_controllers(opts, profile=None):
    """Return every VM in the inventory that has a USB controller device.

    Mirrors the KB-316384 PowerCLI audit sweep (``Get-VM | ? {...}``), but
    across the whole inventory in one call rather than one VM at a time.
    Each entry is ``{"vm", "moid", "connected", "devices"}``; *connected*
    matches ``VirtualMachine.runtime.connectionState == "connected"``, the
    same check the reference script makes before attempting a removal.
    """
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    try:
        out = []
        for vm in container.view:
            if not vm.config:
                continue
            devices = _devices(vm, _USB_CONTROLLER_TYPES)
            if devices:
                out.append(
                    {
                        "vm": vm.name,
                        "moid": vm._moId,  # noqa: SLF001
                        "connected": vm.runtime.connectionState == "connected",
                        "devices": [_device_summary(d) for d in devices],
                    }
                )
        return out
    finally:
        container.Destroy()
