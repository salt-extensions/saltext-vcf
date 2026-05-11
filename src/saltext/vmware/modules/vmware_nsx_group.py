"""Execution module for NSX security groups."""

from saltext.vmware.clients import nsx_group as r

__virtualname__ = "vmware_nsx_group"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List groups in the default domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_group.list_

    """
    return r.list_(__opts__, profile=profile)


def get(group, profile=None):
    """Return a group by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_group.get <group>

    """
    return r.get(__opts__, group, profile=profile)


def create(group, profile=None, **spec):
    """Create or update a group (PUT).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_group.create <group>

    """
    return r.create(__opts__, group, profile=profile, **spec)


def delete(group, profile=None):
    """Delete a group by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_group.delete <group>

    """
    return r.delete(__opts__, group, profile=profile)
