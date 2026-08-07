"""Execution module for ESXi network coredump (netdump)."""

from saltext.vcf.clients import esxi_netdump as c

__virtualname__ = "vcf_esxi_netdump"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_netdump.get

    """
    return c.get(__opts__, profile=profile)


def set_network(interface_name, server_ip, server_port, profile=None):
    """Set network.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_netdump.set_network vmk0 10.0.0.5 6500

    """
    return c.set_network(__opts__, interface_name, server_ip, server_port, profile=profile)


def set_enabled(enabled, profile=None):
    """Set enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_netdump.set_enabled True

    """
    return c.set_enabled(__opts__, enabled, profile=profile)
