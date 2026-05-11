"""Execution module for NSX IP blocks."""

from saltext.vmware.clients import nsx_ip_block as c

__virtualname__ = "vmware_nsx_ip_block"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_ip_block.list_

    """
    return c.list_(__opts__, profile=profile)


def get(block_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_ip_block.get <block_id>

    """
    return c.get(__opts__, block_id, profile=profile)


def create(block_id, cidr, profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_ip_block.create <block_id> <cidr>

    """
    return c.create(__opts__, block_id, cidr, profile=profile, **spec)


def delete(block_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_ip_block.delete <block_id>

    """
    return c.delete(__opts__, block_id, profile=profile)
