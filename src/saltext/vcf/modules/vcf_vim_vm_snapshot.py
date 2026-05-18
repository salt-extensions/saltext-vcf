"""Execution module for VM snapshots (SOAP — REST has no snapshot surface)."""

from saltext.vcf.clients import vim_vm_snapshot as c

__virtualname__ = "vcf_vim_vm_snapshot"


def __virtual__():
    return __virtualname__


def list_(vm, profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.list_ <vm>

    """
    return c.list_(__opts__, vm, profile=profile)


def current(vm, profile=None):
    """Current.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.current <vm>

    """
    return c.current(__opts__, vm, profile=profile)


def create(vm, name, description="", memory=False, quiesce=False, vss_options=None, profile=None):
    """Create.

    Pass ``vss_options`` as a dict to use Windows VSS quiesce
    (``CreateSnapshotEx_Task`` with WindowsQuiesceSpec).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.create <vm> <name> <description> <memory> <quiesce>

    """
    return c.create(
        __opts__,
        vm,
        name,
        description=description,
        memory=memory,
        quiesce=quiesce,
        vss_options=vss_options,
        profile=profile,
    )


def revert(vm, snapshot_name, suppress_power_on=False, profile=None):
    """Revert.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.revert <vm> <snapshot_name> <suppress_power_on>

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

        salt '*' vcf_vim_vm_snapshot.remove <vm> <snapshot_name> <remove_children>

    """
    return c.remove(__opts__, vm, snapshot_name, remove_children=remove_children, profile=profile)


def remove_all(vm, profile=None):
    """Remove all.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.remove_all <vm>

    """
    return c.remove_all(__opts__, vm, profile=profile)


def consolidate(vm, profile=None):
    """Consolidate VM disks (merge orphaned snapshot deltas).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.consolidate <vm>

    """
    return c.consolidate(__opts__, vm, profile=profile)


def state(vm, snapshot_name, profile=None):
    """Return ``{present, is_current, has_memory, has_quiesce, children}`` for a named snapshot.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_snapshot.state <vm> <snapshot_name>

    """
    return c.state(__opts__, vm, snapshot_name, profile=profile)
