"""Execution module for cluster DRS rules + VM/host groups (SOAP)."""

from saltext.vmware.clients import vim_drs_rule as c

__virtualname__ = "vmware_vim_drs_rule"


def __virtual__():
    return __virtualname__


def list_(cluster, profile=None):
    """List all DRS rules on *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.list_ domain-c9
    """
    return c.list_(__opts__, cluster, profile=profile)


def get(cluster, name, profile=None):
    """Return one DRS rule by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.get domain-c9 keep-web-apart
    """
    return c.get(__opts__, cluster, name, profile=profile)


def get_or_none(cluster, name, profile=None):
    """Return the rule or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.get_or_none domain-c9 keep-web-apart
    """
    return c.get_or_none(__opts__, cluster, name, profile=profile)


def create_vm_affinity(cluster, name, vm_moids, enabled=True, mandatory=False, profile=None):
    """Create a VM-VM affinity rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.create_vm_affinity domain-c9 keep-pair '["vm-100","vm-101"]'
    """
    return c.create_vm_affinity(
        __opts__, cluster, name, vm_moids, enabled=enabled, mandatory=mandatory, profile=profile
    )


def create_vm_anti_affinity(cluster, name, vm_moids, enabled=True, mandatory=False, profile=None):
    """Create a VM-VM anti-affinity rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.create_vm_anti_affinity domain-c9 keep-apart '["vm-100","vm-200"]'
    """
    return c.create_vm_anti_affinity(
        __opts__, cluster, name, vm_moids, enabled=enabled, mandatory=mandatory, profile=profile
    )


def create_vm_host(
    cluster,
    name,
    vm_group_name,
    host_group_name,
    affine=True,
    mandatory=False,
    enabled=True,
    profile=None,
):
    """Create a VM-Host rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.create_vm_host domain-c9 pin-prod prod-vms prod-hosts affine=true
    """
    return c.create_vm_host(
        __opts__,
        cluster,
        name,
        vm_group_name,
        host_group_name,
        affine=affine,
        mandatory=mandatory,
        enabled=enabled,
        profile=profile,
    )


def update(cluster, name, enabled=None, mandatory=None, vm_moids=None, profile=None):
    """Update a rule's enabled/mandatory flags and/or VM membership.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.update domain-c9 keep-apart enabled=false
    """
    return c.update(
        __opts__,
        cluster,
        name,
        enabled=enabled,
        mandatory=mandatory,
        vm_moids=vm_moids,
        profile=profile,
    )


def delete(cluster, name, profile=None):
    """Delete a rule by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.delete domain-c9 keep-apart
    """
    return c.delete(__opts__, cluster, name, profile=profile)


# Groups


def list_groups(cluster, profile=None):
    """List VM and host groups on *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.list_groups domain-c9
    """
    return c.list_groups(__opts__, cluster, profile=profile)


def create_vm_group(cluster, name, vm_moids, profile=None):
    """Create a VM group.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.create_vm_group domain-c9 prod-vms '["vm-100","vm-101"]'
    """
    return c.create_vm_group(__opts__, cluster, name, vm_moids, profile=profile)


def create_host_group(cluster, name, host_moids, profile=None):
    """Create a host group.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.create_host_group domain-c9 prod-hosts '["host-100"]'
    """
    return c.create_host_group(__opts__, cluster, name, host_moids, profile=profile)


def delete_group(cluster, name, profile=None):
    """Delete a VM or host group by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_drs_rule.delete_group domain-c9 prod-vms
    """
    return c.delete_group(__opts__, cluster, name, profile=profile)
