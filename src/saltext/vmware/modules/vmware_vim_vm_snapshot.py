"""Execution module for VM snapshots (SOAP — REST has no snapshot surface)."""

from saltext.vmware.clients import vim_vm_snapshot as c

__virtualname__ = "vmware_vim_vm_snapshot"


def __virtual__():
    return __virtualname__


def list_(vm, profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_snapshot.list_ <vm>

    """
    return c.list_(__opts__, vm, profile=profile)


def current(vm, profile=None):
    """Current.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_snapshot.current <vm>

    """
    return c.current(__opts__, vm, profile=profile)


def create(vm, name, description="", memory=False, quiesce=False, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_snapshot.create <vm> <name> <description> <memory> <quiesce>

    """
    return c.create(
        __opts__,
        vm,
        name,
        description=description,
        memory=memory,
        quiesce=quiesce,
        profile=profile,
    )


def revert(vm, snapshot_name, suppress_power_on=False, profile=None):
    """Revert.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_snapshot.revert <vm> <snapshot_name> <suppress_power_on>

    """
    return c.revert(
        __opts__,
        vm,
        snapshot_name,
        suppress_power_on=suppress_power_on,
        profile=profile,
    )


def remove(vm, snapshot_name, remove_children=False, profile=None):
    """Remove.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_snapshot.remove <vm> <snapshot_name> <remove_children>

    """
    return c.remove(__opts__, vm, snapshot_name, remove_children=remove_children, profile=profile)


def remove_all(vm, profile=None):
    """Remove all.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_snapshot.remove_all <vm>

    """
    return c.remove_all(__opts__, vm, profile=profile)
