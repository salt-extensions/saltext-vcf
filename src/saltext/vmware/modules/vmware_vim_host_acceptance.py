"""Execution module for ESXi VIB acceptance level."""

from saltext.vmware.clients import vim_host_acceptance as c

__virtualname__ = "vmware_vim_host_acceptance"


def __virtual__():
    return __virtualname__


def get(host, profile=None):
    """Return the host's current acceptance level.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_acceptance.get <host>
    """
    return c.get(__opts__, host, profile=profile)


def set_(host, level, profile=None):
    """Set the host's acceptance level.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_acceptance.set_ <host> community
    """
    return c.set_(__opts__, host, level, profile=profile)
