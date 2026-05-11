"""Execution module for NSX layer-7 context profiles."""

from saltext.vmware.clients import nsx_context_profile as c

__virtualname__ = "vmware_nsx_context_profile"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_context_profile.list_

    """
    return c.list_(__opts__, profile=profile)


def get(profile_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_context_profile.get <profile_id>

    """
    return c.get(__opts__, profile_id, profile=profile)


def create(profile_id, profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_context_profile.create <profile_id>

    """
    return c.create(__opts__, profile_id, profile=profile, **spec)


def delete(profile_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_context_profile.delete <profile_id>

    """
    return c.delete(__opts__, profile_id, profile=profile)
