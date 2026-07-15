"""VM disk lifecycle via SOAP ``VirtualMachine.ReconfigVM_Task``.

REST has no disk-add/remove/resize surface in VCF 9.x for VirtualDisks;
the canonical path is a ``VirtualDeviceConfigSpec`` reconfigure.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _vm(opts, vm_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    try:
        for vm in container.view:
            if vm_id_or_name in (vm._moId, vm.name):  # noqa: SLF001
                return vm
    finally:
        container.Destroy()
    raise LookupError(f"VM {vm_id_or_name!r} not found")


def list_(opts, vm_id_or_name, profile=None):
    """Return every VirtualDisk on the VM as a list of dicts."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    out = []
    for dev in vm.config.hardware.device or []:
        if isinstance(dev, vim.vm.device.VirtualDisk):
            backing = dev.backing
            out.append(
                {
                    "key": dev.key,
                    "label": dev.deviceInfo.label,
                    "summary": dev.deviceInfo.summary,
                    "capacity_kb": dev.capacityInKB,
                    "capacity_bytes": dev.capacityInBytes,
                    "unit_number": dev.unitNumber,
                    "controller_key": dev.controllerKey,
                    "file_name": getattr(backing, "fileName", None),
                    "disk_mode": getattr(backing, "diskMode", None),
                    "thin": getattr(backing, "thinProvisioned", None),
                    "eager_scrub": getattr(backing, "eagerlyScrub", None),
                    "datastore_moid": (
                        backing.datastore._moId  # noqa: SLF001
                        if getattr(backing, "datastore", None)
                        else None
                    ),
                }
            )
    return out


def add(
    opts,
    vm_id_or_name,
    size_gb,
    *,
    datastore_moid=None,
    controller_key=None,
    unit_number=None,
    disk_mode="persistent",
    thin=True,
    eager_scrub=False,
    profile=None,
):
    """Add a new VirtualDisk to *vm_id_or_name*.

    Returns the task moId.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    controller_key = controller_key or _default_controller_key(vm)
    if unit_number is None:
        unit_number = _next_unit_number(vm, controller_key)

    backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
        diskMode=disk_mode,
        thinProvisioned=thin,
        eagerlyScrub=eager_scrub,
        fileName="",
    )
    if datastore_moid:
        backing.datastore = vim.Datastore(datastore_moid, None)

    disk = vim.vm.device.VirtualDisk(
        key=-1,
        controllerKey=controller_key,
        unitNumber=unit_number,
        capacityInKB=int(size_gb) * 1024 * 1024,
        backing=backing,
    )
    spec = vim.vm.ConfigSpec(
        deviceChange=[
            vim.vm.device.VirtualDeviceSpec(
                operation="add",
                fileOperation="create",
                device=disk,
            )
        ]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def resize(opts, vm_id_or_name, disk_key, size_gb, profile=None):
    """Resize a VirtualDisk identified by its integer ``key``."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    disk = _find_disk(vm, disk_key)
    disk.capacityInKB = int(size_gb) * 1024 * 1024
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="edit", device=disk)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def remove(opts, vm_id_or_name, disk_key, *, destroy_files=False, profile=None):
    """Remove a VirtualDisk by key.

    When *destroy_files* is True, the backing VMDK is deleted from
    the datastore. Otherwise the device is detached and the file kept.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    disk = _find_disk(vm, disk_key)
    device_spec = vim.vm.device.VirtualDeviceSpec(operation="remove", device=disk)
    if destroy_files:
        device_spec.fileOperation = "destroy"
    spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def _default_controller_key(vm):
    for dev in vm.config.hardware.device or []:
        if isinstance(dev, vim.vm.device.VirtualSCSIController):
            return dev.key
    raise LookupError("no SCSI controller on VM")


def _next_unit_number(vm, controller_key):
    used = set()
    for dev in vm.config.hardware.device or []:
        if isinstance(dev, vim.vm.device.VirtualDisk) and dev.controllerKey == controller_key:
            used.add(dev.unitNumber)
    # SCSI unit 7 is reserved for the controller itself
    for candidate in range(16):
        if candidate == 7:
            continue
        if candidate not in used:
            return candidate
    raise ValueError(f"no free unit number on controller {controller_key}")


def _find_disk(vm, key):
    for dev in vm.config.hardware.device or []:
        if isinstance(dev, vim.vm.device.VirtualDisk) and dev.key == int(key):
            return dev
    raise LookupError(f"disk key {key!r} not found on VM {vm.name!r}")
