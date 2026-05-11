"""Execution module for VM migrate / relocate (A5)."""

from saltext.vmware.clients import vim_vm_migrate as m

__virtualname__ = "vmware_vim_vm_migrate"


def __virtual__():
    return __virtualname__


def migrate(vm, host=None, resource_pool=None, priority="default", state=None, profile=None):
    """vMotion a VM. At least one of *host* / *resource_pool* must be set.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_migrate.migrate <vm> host=esxi-2
    """
    return m.migrate(
        __opts__,
        vm,
        host=host,
        resource_pool=resource_pool,
        priority=priority,
        state=state,
        profile=profile,
    )


def relocate(
    vm,
    host=None,
    resource_pool=None,
    datastore=None,
    folder=None,
    disk_format=None,
    priority="default",
    profile=None,
):
    """Combined vMotion + Storage vMotion + folder move via RelocateVM_Task.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_migrate.relocate <vm> host=esxi-2 datastore=vsan
    """
    return m.relocate(
        __opts__,
        vm,
        host=host,
        resource_pool=resource_pool,
        datastore=datastore,
        folder=folder,
        disk_format=disk_format,
        priority=priority,
        profile=profile,
    )
