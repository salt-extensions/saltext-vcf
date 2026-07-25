"""Execution module for NSX Management API — cluster status and API VIP."""

from saltext.vcf.clients import nsx_cluster as c

__virtualname__ = "vcf_nsx_cluster"


def __virtual__():
    return __virtualname__


def status(profile=None):
    """Status.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_cluster.status

    """
    return c.status(__opts__, profile=profile)


def api_virtual_ip_get(profile=None):
    """Return the current management-plane cluster VIP.

    Response ``ip_address`` is empty when no VIP is configured.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_cluster.api_virtual_ip_get

    """
    return c.api_virtual_ip_get(__opts__, profile=profile)


def api_virtual_ip_set(ip_address, profile=None):
    """Set the management-plane cluster VIP.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_cluster.api_virtual_ip_set 10.10.10.100

    """
    return c.api_virtual_ip_set(__opts__, ip_address, profile=profile)


def api_virtual_ip_clear(profile=None):
    """Clear the management-plane cluster VIP.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_cluster.api_virtual_ip_clear

    """
    return c.api_virtual_ip_clear(__opts__, profile=profile)
