"""Execution module for vCenter hosts."""

from saltext.vcf.clients import vcenter_host as r

__virtualname__ = "vcf_vcenter_host"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List ESXi hosts known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_host.list_

    """
    return r.list_(__opts__, profile=profile)


def get(host, profile=None):
    """Return details for a single host by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_host.get <host>

    """
    return r.get(__opts__, host, profile=profile)


def enter_maintenance(host, profile=None):
    """Put a host into maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_host.enter_maintenance <host>

    """
    return r.enter_maintenance(__opts__, host, profile=profile)


def exit_maintenance(host, profile=None):
    """Take a host out of maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_host.exit_maintenance <host>

    """
    return r.exit_maintenance(__opts__, host, profile=profile)
