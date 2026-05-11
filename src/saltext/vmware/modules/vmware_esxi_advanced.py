"""Execution module for ESXi advanced system settings."""

from saltext.vmware.clients import esxi_advanced as c

__virtualname__ = "vmware_esxi_advanced"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_advanced.list_

    """
    return c.list_(__opts__, profile=profile)


def get(key, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_advanced.get <key>

    """
    return c.get(__opts__, key, profile=profile)


def set_value(key, value, profile=None):
    """Set value.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_advanced.set_value <key> <value>

    """
    return c.set_value(__opts__, key, value, profile=profile)
