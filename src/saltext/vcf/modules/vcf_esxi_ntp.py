"""Execution module for ESXi NTP configuration."""

from saltext.vcf.clients import esxi_ntp as c

__virtualname__ = "vcf_esxi_ntp"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_ntp.get

    """
    return c.get(__opts__, profile=profile)


def set_servers(servers, profile=None):
    """Set servers.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_ntp.set_servers <servers>

    """
    return c.set_servers(__opts__, servers, profile=profile)


def set_enabled(enabled, profile=None):
    """Set enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_ntp.set_enabled <enabled>

    """
    return c.set_enabled(__opts__, enabled, profile=profile)
