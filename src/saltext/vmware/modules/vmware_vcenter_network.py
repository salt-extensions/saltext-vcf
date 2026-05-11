"""Execution module for vCenter networks."""

from saltext.vmware.clients import vcenter_network as c

__virtualname__ = "vmware_vcenter_network"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_network.list_

    """
    return c.list_(__opts__, profile=profile)
