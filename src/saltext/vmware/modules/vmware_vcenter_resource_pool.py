"""Execution module for vCenter resource pools."""

from saltext.vmware.clients import vcenter_resource_pool as c

__virtualname__ = "vmware_vcenter_resource_pool"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_resource_pool.list_

    """
    return c.list_(__opts__, profile=profile)


def get(rp_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_resource_pool.get <rp_id>

    """
    return c.get(__opts__, rp_id, profile=profile)


def create(name, parent, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_resource_pool.create <name> <parent>

    """
    return c.create(__opts__, name, parent, **spec)


def delete(rp_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_resource_pool.delete <rp_id>

    """
    return c.delete(__opts__, rp_id, profile=profile)
