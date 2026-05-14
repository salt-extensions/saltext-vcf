"""Execution module for SOAP-only resource-pool ops (move + share-level config)."""

from saltext.vmware.clients import vim_resource_pool as c

__virtualname__ = "vmware_vim_resource_pool"


def __virtual__():
    return __virtualname__


def move(rp, target_parent, profile=None):
    """Move *rp* under *target_parent*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_resource_pool.move <rp> <target_parent>

    """
    return c.move(__opts__, rp, target_parent, profile=profile)


def get_shares(rp, profile=None):
    """Return CPU and memory allocation for *rp*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_resource_pool.get_shares <rp>

    """
    return c.get_shares(__opts__, rp, profile=profile)


def set_shares(rp, cpu=None, memory=None, profile=None):
    """Set CPU and/or memory allocation. Each is a dict.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_resource_pool.set_shares <rp> cpu='{shares_level: high}'

    """
    return c.set_shares(__opts__, rp, cpu=cpu, memory=memory, profile=profile)
