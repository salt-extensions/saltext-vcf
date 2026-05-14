"""Execution module for VASA storage providers."""

from saltext.vmware.clients import vim_vasa as c

__virtualname__ = "vmware_vim_vasa"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List registered VASA storage providers.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vasa.list_
    """
    return c.list_(__opts__, profile=profile)


def get(provider_id, profile=None):
    """Return one VASA provider by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vasa.get <provider_id>
    """
    return c.get(__opts__, provider_id, profile=profile)
