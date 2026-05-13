"""SOAP host maintenance mode with evacuation policy.

REST ``/api/vcenter/host`` exposes basic enter/exit (see
:mod:`vcenter_host`); this SOAP variant supports the additional
``evacuatePoweredOffVms``, ``vsanMode``, and timeout fields.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for host in container.view:
            if host_id_or_name in (host._moId, host.name):  # noqa: SLF001
                return host
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


def is_in(opts, host, profile=None):
    """True if the host is currently in maintenance mode."""
    h = _host(opts, host, profile=profile)
    return bool(h.runtime.inMaintenanceMode)


def enter(
    opts,
    host,
    *,
    evacuate_powered_off_vms=False,
    vsan_mode=None,
    timeout=0,
    profile=None,
):
    """Enter maintenance mode. Returns the vim.Task moId.

    *vsan_mode* — one of ``ensureObjectAccessibility``,
    ``evacuateAllData``, or ``noAction`` (vSAN cluster hosts only).
    *timeout* — 0 means wait forever.
    """
    h = _host(opts, host, profile=profile)
    spec = None
    if vsan_mode is not None:
        spec = vim.host.MaintenanceSpec()
        spec.vsanMode = vim.vsan.host.DecommissionMode(objectAction=vsan_mode)
    if spec is not None:
        task = h.EnterMaintenanceMode_Task(
            timeout=int(timeout),
            evacuatePoweredOffVms=bool(evacuate_powered_off_vms),
            maintenanceSpec=spec,
        )
    else:
        task = h.EnterMaintenanceMode_Task(
            timeout=int(timeout),
            evacuatePoweredOffVms=bool(evacuate_powered_off_vms),
        )
    return task._moId  # noqa: SLF001


def exit_(opts, host, *, timeout=0, profile=None):
    """Exit maintenance mode. Returns the vim.Task moId."""
    h = _host(opts, host, profile=profile)
    task = h.ExitMaintenanceMode_Task(timeout=int(timeout))
    return task._moId  # noqa: SLF001
