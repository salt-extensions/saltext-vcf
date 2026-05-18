"""First-Class Disks (FCD / Improved Virtual Disks) via ``VStorageObjectManager``.

FCDs are vSphere objects that wrap a VMDK and live independently of any VM —
used as persistent volumes for Tanzu / k8s, and as standalone disks for
multi-attach or migration workflows.

Reference:
https://developer.broadcom.com/xapis/vsphere-automation-api/latest/vim/com.vmware.vim.cluster.vstorageobjectmgr/
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _vsom(opts, profile=None):
    return soap.content(opts, profile=profile).vStorageObjectManager


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


def _find_vm(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    try:
        for vm in container.view:
            if name_or_id in (vm._moId, vm.name):  # noqa: SLF001
                return vm
    finally:
        container.Destroy()
    raise LookupError(f"VM {name_or_id!r} not found")


def _to_dict(obj):
    """Convert a ``vim.vslm.VStorageObject`` to a serializable dict."""
    cfg = obj.config
    backing = cfg.backing
    return {
        "id": cfg.id.id,
        "name": cfg.name,
        "capacity_bytes": int(cfg.capacityInMB) * 1024 * 1024,
        "create_time": cfg.createTime.isoformat() if cfg.createTime else None,
        "keep_after_delete_vm": bool(getattr(cfg, "keepAfterDeleteVm", False)),
        "consumption_type": list(cfg.consumptionType or []),
        "consumer_id": [c.id for c in (getattr(cfg, "consumerId", None) or [])],
        "iofilter": list(cfg.iofilter or []),
        "datastore": (
            backing.datastore._moId if backing and backing.datastore else None
        ),  # noqa: SLF001
        "file_path": getattr(backing, "filePath", None),
        "provisioning_type": getattr(backing, "provisioningType", None),
    }


def list_(opts, datastore, profile=None):
    """Return every FCD on *datastore* as a list of dicts."""
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    ids = vsom.ListVStorageObject(datastore=ds) or []
    out = []
    for vsid in ids:
        try:
            obj = vsom.RetrieveVStorageObject(id=vsid, datastore=ds)
            out.append(_to_dict(obj))
        except vim.fault.NotFound:
            continue
    return out


def get(opts, vstorage_object_id, datastore, profile=None):
    """Return one FCD by id."""
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    return _to_dict(vsom.RetrieveVStorageObject(id=vid, datastore=ds))


def get_or_none(opts, vstorage_object_id, datastore, profile=None):
    try:
        return get(opts, vstorage_object_id, datastore, profile=profile)
    except (LookupError, vim.fault.NotFound):
        return None


def create(
    opts,
    name,
    datastore,
    capacity_gb,
    *,
    provisioning="thin",
    profile_id=None,
    keep_after_delete_vm=False,
    profile=None,
):
    """Create an FCD on *datastore*. Returns the vim.Task moId.

    *provisioning* — ``thin``, ``eagerZeroedThick``, or ``lazyZeroedThick``.
    *profile_id* — optional SPBM policy ID list.
    """
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    spec = vim.vslm.CreateSpec()
    spec.name = name
    spec.capacityInMB = int(capacity_gb) * 1024
    spec.keepAfterDeleteVm = bool(keep_after_delete_vm)
    backing = vim.vslm.CreateSpec.DiskFileBackingSpec()
    backing.datastore = ds
    backing.provisioningType = provisioning
    spec.backingSpec = backing
    if profile_id:
        spec.profile = [
            vim.vm.DefinedProfileSpec(profileId=pid)
            for pid in (profile_id if isinstance(profile_id, list) else [profile_id])
        ]
    task = vsom.CreateDisk_Task(spec=spec)
    return task._moId  # noqa: SLF001


def delete(opts, vstorage_object_id, datastore, profile=None):
    """Delete an FCD. Returns the vim.Task moId."""
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    task = vsom.DeleteVStorageObject_Task(id=vid, datastore=ds)
    return task._moId  # noqa: SLF001


def rename(opts, vstorage_object_id, datastore, new_name, profile=None):
    """Rename an FCD."""
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    vsom.RenameVStorageObject(id=vid, datastore=ds, name=new_name)
    return True


def extend(opts, vstorage_object_id, datastore, new_capacity_gb, profile=None):
    """Grow an FCD to *new_capacity_gb*. Returns the vim.Task moId."""
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    task = vsom.ExtendDisk_Task(id=vid, datastore=ds, newCapacityInMB=int(new_capacity_gb) * 1024)
    return task._moId  # noqa: SLF001


def register(opts, datastore, path, name, profile=None):  # pylint: disable=unused-argument
    """Register an existing VMDK as an FCD.

    *datastore* is accepted for API symmetry but RegisterDisk derives the
    datastore from the VMDK *path* itself.
    """
    vsom = _vsom(opts, profile=profile)
    obj = vsom.RegisterDisk(path=path, name=name)
    return _to_dict(obj)


def set_keep_after_delete_vm(opts, vstorage_object_id, datastore, keep, profile=None):
    """Set whether the FCD survives the deletion of any VM it's attached to."""
    ds = _find_datastore(opts, datastore, profile=profile)
    vsom = _vsom(opts, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    if keep:
        vsom.SetVStorageObjectControlFlags(id=vid, datastore=ds, controlFlags=["keepAfterDeleteVm"])
    else:
        vsom.ClearVStorageObjectControlFlags(
            id=vid, datastore=ds, controlFlags=["keepAfterDeleteVm"]
        )
    return True


def attach_to_vm(
    opts, vm, vstorage_object_id, datastore, *, controller_key=None, unit_number=None, profile=None
):
    """Attach an FCD to a VM as an additional virtual disk.

    Returns the vim.Task moId. *controller_key* and *unit_number* may be left
    None and vSphere will pick.
    """
    vm_obj = _find_vm(opts, vm, profile=profile)
    ds = _find_datastore(opts, datastore, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    kwargs = {"diskId": vid, "datastore": ds}
    if controller_key is not None:
        kwargs["controllerKey"] = int(controller_key)
    if unit_number is not None:
        kwargs["unitNumber"] = int(unit_number)
    task = vm_obj.AttachDisk_Task(**kwargs)
    return task._moId  # noqa: SLF001


def detach_from_vm(opts, vm, vstorage_object_id, profile=None):
    """Detach an FCD from a VM (the disk remains, just unhooked)."""
    vm_obj = _find_vm(opts, vm, profile=profile)
    vid = vim.vslm.ID(id=vstorage_object_id)
    task = vm_obj.DetachDisk_Task(diskId=vid)
    return task._moId  # noqa: SLF001
