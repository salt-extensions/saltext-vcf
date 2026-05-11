"""Execution module for NSX Tier-1 gateways."""

from saltext.vmware.clients import nsx_tier1 as r

__virtualname__ = "vmware_nsx_tier1"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List Tier-1 gateways.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_tier1.list_

    """
    return r.list_(__opts__, profile=profile)


def get(tier1, profile=None):
    """Return a Tier-1 gateway by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_tier1.get <tier1>

    """
    return r.get(__opts__, tier1, profile=profile)


def create(tier1, profile=None, **spec):
    """Create or update a Tier-1 gateway (PUT).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_tier1.create <tier1>

    """
    return r.create(__opts__, tier1, profile=profile, **spec)


def delete(tier1, profile=None):
    """Delete a Tier-1 gateway by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_tier1.delete <tier1>

    """
    return r.delete(__opts__, tier1, profile=profile)
