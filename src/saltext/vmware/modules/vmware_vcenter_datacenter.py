"""Execution module for vCenter datacenters."""

from saltext.vmware.clients import vcenter_datacenter as r

__virtualname__ = "vmware_vcenter_datacenter"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List datacenters known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_datacenter.list_

    """
    return r.list_(__opts__, profile=profile)


def get(datacenter, profile=None):
    """Return details for a single datacenter by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_datacenter.get <datacenter>

    """
    return r.get(__opts__, datacenter, profile=profile)


def create(name, folder=None, profile=None):
    """Create a datacenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_datacenter.create <name> <folder>

    """
    return r.create(__opts__, name, folder=folder, profile=profile)


def delete(datacenter, profile=None):
    """Delete a datacenter by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_datacenter.delete <datacenter>

    """
    return r.delete(__opts__, datacenter, profile=profile)
