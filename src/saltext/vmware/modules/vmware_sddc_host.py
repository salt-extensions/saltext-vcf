"""Execution module for SDDC Manager hosts."""

from saltext.vmware.clients import sddc_host as r

__virtualname__ = "vmware_sddc_host"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List hosts in the SDDC inventory.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_host.list_

    """
    return r.list_(__opts__, profile=profile)


def get(host, profile=None):
    """Return details for a single host by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_host.get <host>

    """
    return r.get(__opts__, host, profile=profile)


def commission(host_specs, profile=None):
    """Commission one or more hosts (POST /v1/hosts).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_host.commission <host_specs>

    """
    return r.commission(__opts__, host_specs, profile=profile)


def decommission(host, profile=None):
    """Decommission a host by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_host.decommission <host>

    """
    return r.decommission(__opts__, host, profile=profile)
