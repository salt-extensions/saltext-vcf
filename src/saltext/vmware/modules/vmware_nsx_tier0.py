"""Execution module for NSX Tier-0 gateways."""

from saltext.vmware.clients import nsx_tier0 as r

__virtualname__ = "vmware_nsx_tier0"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List Tier-0 gateways.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_tier0.list_

    """
    return r.list_(__opts__, profile=profile)


def get(tier0, profile=None):
    """Return a Tier-0 gateway by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_tier0.get <tier0>

    """
    return r.get(__opts__, tier0, profile=profile)
