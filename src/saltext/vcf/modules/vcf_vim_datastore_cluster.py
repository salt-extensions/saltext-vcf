"""Execution module for datastore clusters + Storage DRS."""

from saltext.vcf.clients import vim_datastore_cluster as c

__virtualname__ = "vcf_vim_datastore_cluster"


def __virtual__():
    return __virtualname__


# Pod CRUD


def list_(profile=None):
    """List datastore clusters.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.list_
    """
    return c.list_(__opts__, profile=profile)


def get(name_or_id, profile=None):
    """Return one datastore cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.get <name>
    """
    return c.get(__opts__, name_or_id, profile=profile)


def create(name, datacenter, profile=None):
    """Create an empty datastore cluster under *datacenter*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.create prod-storage Datacenter
    """
    return c.create(__opts__, name, datacenter, profile=profile)


def delete(name_or_id, profile=None):
    """Delete a datastore cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.delete <name>
    """
    return c.delete(__opts__, name_or_id, profile=profile)


def add_datastore(pod, datastore, profile=None):
    """Move a datastore into a datastore cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.add_datastore <pod> <datastore>
    """
    return c.add_datastore(__opts__, pod, datastore, profile=profile)


def remove_datastore(pod, datastore, datacenter, profile=None):
    """Move a datastore out of a datastore cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.remove_datastore <pod> <datastore> <datacenter>
    """
    return c.remove_datastore(__opts__, pod, datastore, datacenter, profile=profile)


# SDRS config


def sdrs_get(pod, profile=None):
    """Return pod-wide SDRS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_get <pod>
    """
    return c.sdrs_get(__opts__, pod, profile=profile)


def sdrs_set(
    pod,
    enabled=None,
    automation_level=None,
    io_load_balance_enabled=None,
    space_utilization_threshold=None,
    profile=None,
):
    """Update pod-wide SDRS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_set <pod> enabled=True automation_level=automated
    """
    return c.sdrs_set(
        __opts__,
        pod,
        enabled=enabled,
        automation_level=automation_level,
        io_load_balance_enabled=io_load_balance_enabled,
        space_utilization_threshold=space_utilization_threshold,
        profile=profile,
    )


# Per-VM overrides


def sdrs_vm_override_list(pod, profile=None):
    """List per-VM SDRS overrides on a datastore cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_vm_override_list <pod>
    """
    return c.sdrs_vm_override_list(__opts__, pod, profile=profile)


def sdrs_vm_override_set(
    pod, vm_moid, behavior=None, enabled=None, intra_vm_affinity=None, profile=None
):
    """Add / update an SDRS override for a single VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_vm_override_set <pod> <vm_moid> behavior=manual
    """
    return c.sdrs_vm_override_set(
        __opts__,
        pod,
        vm_moid,
        behavior=behavior,
        enabled=enabled,
        intra_vm_affinity=intra_vm_affinity,
        profile=profile,
    )


def sdrs_vm_override_remove(pod, vm_moid, profile=None):
    """Remove a VM's SDRS override.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_vm_override_remove <pod> <vm_moid>
    """
    return c.sdrs_vm_override_remove(__opts__, pod, vm_moid, profile=profile)


def sdrs_rule_list(pod, profile=None):
    """List SDRS rules on *pod*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_rule_list <pod>
    """
    return c.sdrs_rule_list(__opts__, pod, profile=profile)


def sdrs_rule_get(pod, name, profile=None):
    """Return one SDRS rule by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_rule_get <pod> <name>
    """
    return c.sdrs_rule_get(__opts__, pod, name, profile=profile)


def sdrs_rule_create_vm_anti_affinity(
    pod, name, vm_moids, enabled=True, mandatory=False, profile=None
):
    """Create an SDRS VM anti-affinity rule (keeps VMDKs on different datastores).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_rule_create_vm_anti_affinity <pod> <name> '["vm-1","vm-2"]'
    """
    return c.sdrs_rule_create_vm_anti_affinity(
        __opts__, pod, name, vm_moids, enabled=enabled, mandatory=mandatory, profile=profile
    )


def sdrs_rule_create_vm_affinity(pod, name, vm_moids, enabled=True, mandatory=False, profile=None):
    """Create an SDRS VM affinity rule (keeps VMDKs on the same datastore).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_rule_create_vm_affinity <pod> <name> '["vm-1","vm-2"]'
    """
    return c.sdrs_rule_create_vm_affinity(
        __opts__, pod, name, vm_moids, enabled=enabled, mandatory=mandatory, profile=profile
    )


def sdrs_rule_delete(pod, name, profile=None):
    """Delete an SDRS rule by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore_cluster.sdrs_rule_delete <pod> <name>
    """
    return c.sdrs_rule_delete(__opts__, pod, name, profile=profile)
