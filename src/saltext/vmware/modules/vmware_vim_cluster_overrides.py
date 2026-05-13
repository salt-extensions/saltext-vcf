"""Execution module for per-VM / per-host cluster overrides."""

from saltext.vmware.clients import vim_cluster_overrides as c

__virtualname__ = "vmware_vim_cluster_overrides"


def __virtual__():
    return __virtualname__


# DRS VM overrides


def drs_vm_list(cluster, profile=None):
    """List per-VM DRS overrides.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.drs_vm_list <cluster>
    """
    return c.drs_vm_list(__opts__, cluster, profile=profile)


def drs_vm_set(cluster, vm_moid, behavior, enabled=True, profile=None):
    """Add / update a DRS override for a single VM.

    *behavior*: ``manual`` | ``partiallyAutomated`` | ``fullyAutomated`` | ``disabled``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.drs_vm_set <cluster> <vm_moid> manual
    """
    return c.drs_vm_set(__opts__, cluster, vm_moid, behavior, enabled=enabled, profile=profile)


def drs_vm_remove(cluster, vm_moid, profile=None):
    """Remove a VM's DRS override.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.drs_vm_remove <cluster> <vm_moid>
    """
    return c.drs_vm_remove(__opts__, cluster, vm_moid, profile=profile)


# HA VM overrides


def ha_vm_list(cluster, profile=None):
    """List per-VM HA overrides.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.ha_vm_list <cluster>
    """
    return c.ha_vm_list(__opts__, cluster, profile=profile)


def ha_vm_set(cluster, vm_moid, restart_priority=None, isolation_response=None, profile=None):
    """Add / update an HA override for a single VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.ha_vm_set <cluster> <vm_moid> restart_priority=high
    """
    return c.ha_vm_set(
        __opts__,
        cluster,
        vm_moid,
        restart_priority=restart_priority,
        isolation_response=isolation_response,
        profile=profile,
    )


def ha_vm_remove(cluster, vm_moid, profile=None):
    """Remove a VM's HA override.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.ha_vm_remove <cluster> <vm_moid>
    """
    return c.ha_vm_remove(__opts__, cluster, vm_moid, profile=profile)


# DPM host overrides


def dpm_host_list(cluster, profile=None):
    """List per-host DPM overrides.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.dpm_host_list <cluster>
    """
    return c.dpm_host_list(__opts__, cluster, profile=profile)


def dpm_host_set(cluster, host_moid, behavior, enabled=True, profile=None):
    """Add / update a DPM override for a single host.

    *behavior*: ``manual`` | ``automated``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.dpm_host_set <cluster> <host_moid> manual
    """
    return c.dpm_host_set(__opts__, cluster, host_moid, behavior, enabled=enabled, profile=profile)


def dpm_host_remove(cluster, host_moid, profile=None):
    """Remove a host's DPM override.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_overrides.dpm_host_remove <cluster> <host_moid>
    """
    return c.dpm_host_remove(__opts__, cluster, host_moid, profile=profile)
