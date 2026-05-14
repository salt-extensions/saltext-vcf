"""vSphere vApp container management via ``vim.VirtualApp``.

A vApp is a special kind of resource pool that wraps a group of VMs with
startup/shutdown ordering and metadata. Created via
``ResourcePool.CreateVApp`` or ``Folder.CreateVApp``.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def _content(opts, profile=None):
    return soap.content(opts, profile=profile)


def _find_vapp(opts, name_or_id, profile=None):
    content = _content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualApp], True)
    try:
        for v in container.view:
            if name_or_id in (v._moId, v.name):  # noqa: SLF001
                return v
    finally:
        container.Destroy()
    raise LookupError(f"vApp {name_or_id!r} not found")


def _find_resource_pool(opts, name_or_id, profile=None):
    content = _content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.ResourcePool], True
    )
    try:
        for rp in container.view:
            if name_or_id in (rp._moId, rp.name):  # noqa: SLF001
                return rp
    finally:
        container.Destroy()
    raise LookupError(f"resource pool {name_or_id!r} not found")


def _to_dict(vapp):
    summary = vapp.summary
    cfg = vapp.vAppConfig
    return {
        "id": vapp._moId,  # noqa: SLF001
        "name": vapp.name,
        "parent": vapp.parent._moId if vapp.parent else None,  # noqa: SLF001
        "overall_status": str(summary.overallStatus) if summary else None,
        "vm_count": len(list(vapp.vm)) if vapp.vm else 0,
        "annotation": cfg.annotation if cfg else None,
        "product": (
            [
                {"name": p.name, "vendor": p.vendor, "version": p.version}
                for p in (cfg.product or [])
            ]
            if cfg
            else []
        ),
    }


def list_(opts, profile=None):
    content = _content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualApp], True)
    try:
        return [_to_dict(v) for v in container.view]
    finally:
        container.Destroy()


def get(opts, name_or_id, profile=None):
    return _to_dict(_find_vapp(opts, name_or_id, profile=profile))


def get_or_none(opts, name_or_id, profile=None):
    try:
        return get(opts, name_or_id, profile=profile)
    except LookupError:
        return None


def create(opts, name, parent_resource_pool, *, annotation=None, profile=None):
    """Create a vApp under *parent_resource_pool* (resource-pool moId or name).

    Synchronous; returns the new vApp dict.
    """
    rp = _find_resource_pool(opts, parent_resource_pool, profile=profile)
    cfg_spec = vim.vApp.VAppConfigSpec()
    if annotation is not None:
        cfg_spec.annotation = annotation
    res_spec = vim.ResourceConfigSpec()
    res_spec.cpuAllocation = vim.ResourceAllocationInfo(
        reservation=0, expandableReservation=True, limit=-1, shares=vim.SharesInfo(level="normal")
    )
    res_spec.memoryAllocation = vim.ResourceAllocationInfo(
        reservation=0, expandableReservation=True, limit=-1, shares=vim.SharesInfo(level="normal")
    )
    new_vapp = rp.CreateVApp(name=name, resSpec=res_spec, configSpec=cfg_spec, vmFolder=None)
    return _to_dict(new_vapp)


def power_on(opts, name_or_id, profile=None):
    """Power on all VMs in the vApp. Returns the vim.Task moId."""
    v = _find_vapp(opts, name_or_id, profile=profile)
    task = v.PowerOnVApp_Task()
    return task._moId  # noqa: SLF001


def power_off(opts, name_or_id, *, force=False, profile=None):
    v = _find_vapp(opts, name_or_id, profile=profile)
    task = v.PowerOffVApp_Task(force=bool(force))
    return task._moId  # noqa: SLF001


def suspend(opts, name_or_id, profile=None):
    v = _find_vapp(opts, name_or_id, profile=profile)
    task = v.SuspendVApp_Task()
    return task._moId  # noqa: SLF001


def delete(opts, name_or_id, profile=None):
    v = _find_vapp(opts, name_or_id, profile=profile)
    task = v.Destroy_Task()
    return task._moId  # noqa: SLF001


def update(opts, name_or_id, *, annotation=None, profile=None):
    """Update vApp metadata fields. Returns the updated vApp dict."""
    v = _find_vapp(opts, name_or_id, profile=profile)
    cfg_spec = vim.vApp.VAppConfigSpec()
    if annotation is not None:
        cfg_spec.annotation = annotation
    v.UpdateVAppConfig(spec=cfg_spec)
    return _to_dict(v)
