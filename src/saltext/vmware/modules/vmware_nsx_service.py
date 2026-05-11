"""Execution module for NSX service definitions."""

from saltext.vmware.clients import nsx_service as c

__virtualname__ = "vmware_nsx_service"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_service.list_

    """
    return c.list_(__opts__, profile=profile)


def get(service, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_service.get <service>

    """
    return c.get(__opts__, service, profile=profile)


def create(service, profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_service.create <service>

    """
    return c.create(__opts__, service, profile=profile, **spec)


def delete(service, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_service.delete <service>

    """
    return c.delete(__opts__, service, profile=profile)
