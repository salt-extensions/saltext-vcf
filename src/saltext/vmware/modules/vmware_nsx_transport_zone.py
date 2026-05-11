"""Execution module for NSX transport zones."""

from saltext.vmware.clients import nsx_transport_zone as c

__virtualname__ = "vmware_nsx_transport_zone"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_transport_zone.list_

    """
    return c.list_(__opts__, profile=profile)


def get(zone_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_transport_zone.get <zone_id>

    """
    return c.get(__opts__, zone_id, profile=profile)
