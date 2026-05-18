"""Execution module for NSX edge clusters."""

from saltext.vcf.clients import nsx_edge_cluster as c

__virtualname__ = "vcf_nsx_edge_cluster"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge_cluster.list_

    """
    return c.list_(__opts__, profile=profile)


def get(cluster_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge_cluster.get <cluster_id>

    """
    return c.get(__opts__, cluster_id, profile=profile)


def create(body, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge_cluster.create <body>

    """
    return c.create(__opts__, body, profile=profile)


def update(cluster_id, body, profile=None):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge_cluster.update <cluster_id> <body>

    """
    return c.update(__opts__, cluster_id, body, profile=profile)


def delete(cluster_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge_cluster.delete <cluster_id>

    """
    return c.delete(__opts__, cluster_id, profile=profile)


def state(cluster_id, profile=None):
    """State.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge_cluster.state <cluster_id>

    """
    return c.state(__opts__, cluster_id, profile=profile)
