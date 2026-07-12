"""Execution module for NSX edge nodes."""

from saltext.vcf.clients import nsx_edge as c

__virtualname__ = "vcf_nsx_edge"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List edge transport nodes.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.list_

    """
    return c.list_(__opts__, profile=profile)


def get(node_id, profile=None):
    """Get an edge transport node.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.get <node_id>

    """
    return c.get(__opts__, node_id, profile=profile)


def get_or_none(node_id, profile=None):
    """Get an edge transport node or return ``None`` on 404.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.get_or_none <node_id>

    """
    return c.get_or_none(__opts__, node_id, profile=profile)


def create(body, profile=None):
    """Create an edge transport node.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.create <body>

    """
    return c.create(__opts__, body, profile=profile)


def update(node_id, body, profile=None):
    """Update an edge transport node.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.update <node_id> <body>

    """
    return c.update(__opts__, node_id, body, profile=profile)


def delete(node_id, profile=None):
    """Delete an edge transport node.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.delete <node_id>

    """
    return c.delete(__opts__, node_id, profile=profile)


def redeploy(node_id, body=None, profile=None):
    """Redeploy an edge transport node.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.redeploy <node_id>

    """
    return c.redeploy(__opts__, node_id, body=body, profile=profile)


def state(node_id, profile=None):
    """Return realization state for the edge transport node.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.state <node_id>

    """
    return c.state(__opts__, node_id, profile=profile)


def cluster_allocation_status(cluster_id, profile=None):
    """Return allocation status for edge nodes in the given cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_edge.cluster_allocation_status <cluster_id>

    """
    return c.cluster_allocation_status(__opts__, cluster_id, profile=profile)
