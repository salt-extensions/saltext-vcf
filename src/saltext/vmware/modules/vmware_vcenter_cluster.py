"""Execution module for vCenter clusters."""

from saltext.vmware.clients import vcenter_cluster as r

__virtualname__ = "vmware_vcenter_cluster"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List clusters known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_cluster.list_

    """
    return r.list_(__opts__, profile=profile)


def get(cluster, profile=None):
    """Return details for a single cluster by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_cluster.get <cluster>

    """
    return r.get(__opts__, cluster, profile=profile)


def create(name, datacenter=None, profile=None, **spec):
    """Create a cluster. *spec* is passed straight to the vCenter API body.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_cluster.create <name> <datacenter>

    """
    return r.create(__opts__, name, datacenter=datacenter, profile=profile, **spec)


def delete(cluster, profile=None):
    """Delete a cluster by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_cluster.delete <cluster>

    """
    return r.delete(__opts__, cluster, profile=profile)
