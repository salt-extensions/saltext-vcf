"""VM migration via SOAP.

Two operations are exposed:

- ``MigrateVM_Task`` — change the compute target (host/cluster/resource pool).
  This is the classic vMotion path.
- ``RelocateVM_Task`` — change anything (host, datastore, folder, resource pool,
  disk format). This is the unified path that subsumes both vMotion and
  Storage vMotion, and is the one Terraform / Ansible typically use.

Both return the task moid; the caller polls vCenter for completion.
"""

from pyVmomi import vim

from saltext.vcf.clients.vim_vm import _find_by_type
from saltext.vcf.clients.vim_vm import _vm

_PRIORITIES = {
    "low": vim.VirtualMachine.MovePriority.lowPriority,
    "default": vim.VirtualMachine.MovePriority.defaultPriority,
    "high": vim.VirtualMachine.MovePriority.highPriority,
}

_POWER_STATES = {
    "poweredOn": vim.VirtualMachine.PowerState.poweredOn,
    "poweredOff": vim.VirtualMachine.PowerState.poweredOff,
    "suspended": vim.VirtualMachine.PowerState.suspended,
}


def migrate(
    opts,
    vm_id_or_name,
    *,
    host=None,
    resource_pool=None,
    priority="default",
    state=None,
    profile=None,
):
    """vMotion *vm* to a new host/pool. Returns the task moid.

    Either *host* or *resource_pool* (or both) must be specified.
    """
    if host is None and resource_pool is None:
        raise ValueError("at least one of host / resource_pool must be set")
    vm = _vm(opts, vm_id_or_name, profile=profile)
    host_ref = (
        _find_by_type(opts, vim.HostSystem, host, profile=profile) if host is not None else None
    )
    pool_ref = (
        _find_by_type(opts, vim.ResourcePool, resource_pool, profile=profile)
        if resource_pool is not None
        else None
    )
    prio = _PRIORITIES.get(priority, _PRIORITIES["default"])
    state_ref = _POWER_STATES[state] if state is not None else None
    task = vm.MigrateVM_Task(pool=pool_ref, host=host_ref, priority=prio, state=state_ref)
    return task._moId  # noqa: SLF001


def relocate(
    opts,
    vm_id_or_name,
    *,
    host=None,
    resource_pool=None,
    datastore=None,
    folder=None,
    disk_format=None,
    priority="default",
    profile=None,
):
    """Unified relocate. Returns the task moid.

    *disk_format* — ``thin`` | ``thick`` | ``eagerZeroedThick`` (passed verbatim
    to ``RelocateSpec.diskMoveType`` style enums); leave ``None`` to inherit.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    spec = vim.vm.RelocateSpec()
    if host is not None:
        spec.host = _find_by_type(opts, vim.HostSystem, host, profile=profile)
    if resource_pool is not None:
        spec.pool = _find_by_type(opts, vim.ResourcePool, resource_pool, profile=profile)
    if datastore is not None:
        spec.datastore = _find_by_type(opts, vim.Datastore, datastore, profile=profile)
    if folder is not None:
        spec.folder = _find_by_type(opts, vim.Folder, folder, profile=profile)
    if disk_format is not None:
        spec.transform = disk_format  # "sparse" | "flat"
    prio = _PRIORITIES.get(priority, _PRIORITIES["default"])
    task = vm.RelocateVM_Task(spec=spec, priority=prio)
    return task._moId  # noqa: SLF001
