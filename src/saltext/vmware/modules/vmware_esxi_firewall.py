"""Execution module for ESXi firewall rules."""

from saltext.vmware.clients import esxi_firewall as c

__virtualname__ = "vmware_esxi_firewall"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_firewall.list_

    """
    return c.list_(__opts__, profile=profile)


def get(rule, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_firewall.get <rule>

    """
    return c.get(__opts__, rule, profile=profile)


def set_enabled(rule, enabled, profile=None):
    """Set enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_firewall.set_enabled <rule> <enabled>

    """
    return c.set_enabled(__opts__, rule, enabled, profile=profile)


def set_allowed_ips(rule, allowed_ips, all_ip=False, profile=None):
    """Set allowed ips.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_firewall.set_allowed_ips <rule> <allowed_ips> <all_ip>

    """
    return c.set_allowed_ips(__opts__, rule, allowed_ips, all_ip=all_ip, profile=profile)
