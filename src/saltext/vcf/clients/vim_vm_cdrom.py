"""VM CD/DVD device lifecycle via SOAP ``VirtualMachine.ReconfigVM_Task``.

Nested-hypervisor installs need an installer ISO attached to a CD-ROM;
this client covers the ``add`` / ``list`` / ``attach_iso`` /
``eject`` / ``remove`` primitives.
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


def _find_datastore(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    try:
        for ds in container.view:
            if name_or_id in (ds._moId, ds.name):  # noqa: SLF001
                return ds
    finally:
        container.Destroy()
    raise LookupError(f"datastore {name_or_id!r} not found")


def _ide_controller_key(vm):
    """Return the key of an IDE controller with a free slot.

    ESXi VMs get two IDE controllers by default; each carries two
    devices.  Returns the first controller with room, or raises.
    """
    ide_controllers = [
        d
        for d in vm.config.hardware.device or []
        if isinstance(d, vim.vm.device.VirtualIDEController)
    ]
    if not ide_controllers:
        raise LookupError("no IDE controller on VM")
    for ctrl in ide_controllers:
        # IDE controllers hold up to two devices (unit 0 and 1).
        if len(ctrl.device or []) < 2:
            return ctrl.key
    raise ValueError("all IDE controllers are full")


def list_(opts, vm_id_or_name, profile=None):
    """Return every CD/DVD device on the VM as a list of dicts."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    out = []
    for dev in vm.config.hardware.device or []:
        if not isinstance(dev, vim.vm.device.VirtualCdrom):
            continue
        backing = dev.backing
        out.append(
            {
                "key": dev.key,
                "label": dev.deviceInfo.label,
                "summary": dev.deviceInfo.summary,
                "controller_key": dev.controllerKey,
                "unit_number": dev.unitNumber,
                "backing_kind": type(backing).__name__ if backing else None,
                "iso_path": getattr(backing, "fileName", None),
                "connected": dev.connectable.connected if dev.connectable else None,
                "start_connected": (dev.connectable.startConnected if dev.connectable else None),
            }
        )
    return out


def add(
    opts,
    vm_id_or_name,
    *,
    iso_path=None,
    datastore=None,
    controller_key=None,
    start_connected=True,
    profile=None,
):
    """Add a new CD/DVD to the VM.

    * *iso_path* — ISO path.  Absolute (``[datastore] path/to.iso``)
      or datastore-relative (``isos/foo.iso`` — pair with *datastore*).
      Omit both for an empty CD-ROM.
    * *datastore* — datastore name/MOID to resolve *iso_path* against
      when it's a bare relative path.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    if controller_key is None:
        controller_key = _ide_controller_key(vm)

    cdrom = vim.vm.device.VirtualCdrom(key=-1, controllerKey=controller_key)
    if iso_path:
        if not iso_path.startswith("["):
            if not datastore:
                raise ValueError(
                    "iso_path without a datastore-bracket prefix requires "
                    "datastore= to resolve against"
                )
            ds = _find_datastore(opts, datastore, profile=profile)
            iso_path = f"[{ds.name}] {iso_path.lstrip('/')}"
        backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)
    else:
        backing = vim.vm.device.VirtualCdrom.AtapiBackingInfo(deviceName="")
    cdrom.backing = backing
    cdrom.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
        startConnected=start_connected,
        connected=start_connected,
        allowGuestControl=True,
    )
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="add", device=cdrom)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def attach_iso(
    opts,
    vm_id_or_name,
    iso_path,
    *,
    cdrom_key=None,
    datastore=None,
    profile=None,
):
    """Attach an ISO to an existing CD-ROM device (defaults to the
    first CD-ROM if *cdrom_key* is omitted)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    cdrom = _find_cdrom(vm, cdrom_key)
    if not iso_path.startswith("["):
        if not datastore:
            raise ValueError(
                "iso_path without a datastore-bracket prefix requires "
                "datastore= to resolve against"
            )
        ds = _find_datastore(opts, datastore, profile=profile)
        iso_path = f"[{ds.name}] {iso_path.lstrip('/')}"
    cdrom.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)
    if cdrom.connectable is None:
        cdrom.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    cdrom.connectable.startConnected = True
    cdrom.connectable.connected = True
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="edit", device=cdrom)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def eject(opts, vm_id_or_name, *, cdrom_key=None, profile=None):
    """Detach the ISO from an existing CD-ROM device (leaves the
    device in place, empty)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    cdrom = _find_cdrom(vm, cdrom_key)
    cdrom.backing = vim.vm.device.VirtualCdrom.AtapiBackingInfo(deviceName="")
    if cdrom.connectable:
        cdrom.connectable.connected = False
        cdrom.connectable.startConnected = False
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="edit", device=cdrom)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def remove(opts, vm_id_or_name, cdrom_key, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    cdrom = _find_cdrom(vm, cdrom_key)
    spec = vim.vm.ConfigSpec(
        deviceChange=[vim.vm.device.VirtualDeviceSpec(operation="remove", device=cdrom)]
    )
    task = vm.ReconfigVM_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def _find_cdrom(vm, key):
    cdroms = [
        d for d in vm.config.hardware.device or [] if isinstance(d, vim.vm.device.VirtualCdrom)
    ]
    if key is None:
        if not cdroms:
            raise LookupError(f"no CD-ROM on VM {vm.name!r}")
        return cdroms[0]
    for dev in cdroms:
        if dev.key == int(key):
            return dev
    raise LookupError(f"CD-ROM key {key!r} not found on VM {vm.name!r}")
