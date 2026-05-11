"""Execution module for ESXi services."""

from saltext.vmware.clients import esxi_service as c

__virtualname__ = "vmware_esxi_service"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_service.list_

    """
    return c.list_(__opts__, profile=profile)


def get(service, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_service.get <service>

    """
    return c.get(__opts__, service, profile=profile)


def start(service, profile=None):
    """Start.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_service.start <service>

    """
    return c.start(__opts__, service, profile=profile)


def stop(service, profile=None):
    """Stop.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_service.stop <service>

    """
    return c.stop(__opts__, service, profile=profile)


def restart(service, profile=None):
    """Restart.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_service.restart <service>

    """
    return c.restart(__opts__, service, profile=profile)


def set_policy(service, policy, profile=None):
    """Set startup policy (``ON``, ``OFF``, ``AUTOMATIC``).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_esxi_service.set_policy <service> <policy>

    """
    return c.set_policy(__opts__, service, policy, profile=profile)
