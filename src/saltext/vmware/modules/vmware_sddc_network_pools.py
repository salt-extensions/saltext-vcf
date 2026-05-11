"""Execution module for SDDC Manager network pools."""

from saltext.vmware.clients import sddc_network_pools as c

__virtualname__ = "vmware_sddc_network_pools"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_network_pools.list_

    """
    return c.list_(__opts__, profile=profile)


def get(pool_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_network_pools.get <pool_id>

    """
    return c.get(__opts__, pool_id, profile=profile)


def create(network_pool_spec, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_network_pools.create <network_pool_spec>

    """
    return c.create(__opts__, network_pool_spec, profile=profile)


def delete(pool_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_network_pools.delete <pool_id>

    """
    return c.delete(__opts__, pool_id, profile=profile)
