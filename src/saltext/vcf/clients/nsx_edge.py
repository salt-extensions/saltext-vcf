"""NSX Management API — edge nodes.

Edge NODES are individual transport nodes of type ``EdgeNode`` (as opposed to
:mod:`saltext.vcf.clients.nsx_edge_cluster`, which manages the containing
CLUSTERS). Edge nodes are managed through the shared transport-node API
(``/api/v1/transport-nodes``) filtered on ``node_types=EdgeNode``.

Single-node reads (``get`` / ``get_or_none``) delegate to
:mod:`saltext.vcf.clients.nsx_transport_node` so the 404 handling and endpoint
shape stay in one place. Only the edge-specific behaviour lives here:
``list_`` (adds the ``node_types=EdgeNode`` filter), write endpoints
(``create``/``update``/``delete`` — transport_node has no CRUD), plus
``redeploy`` / ``state`` / ``cluster_allocation_status``.
"""

from saltext.vcf.clients import nsx_transport_node
from saltext.vcf.utils import nsx

PATH = nsx_transport_node.PATH
EDGE_CLUSTERS_PATH = "/api/v1/edge-clusters"


def list_(opts, profile=None):
    """List all edge transport nodes (``node_types=EdgeNode``)."""
    return nsx.api_get(opts, PATH, params={"node_types": "EdgeNode"}, profile=profile)


def get(opts, node_id, profile=None):
    """Get a single edge transport node by id."""
    return nsx_transport_node.get(opts, node_id, profile=profile)


def get_or_none(opts, node_id, profile=None):
    """Return the edge node, or ``None`` if the API responds 404."""
    return nsx_transport_node.get_or_none(opts, node_id, profile=profile)


def create(opts, body, profile=None):
    """Create an edge transport node. *body* is the TransportNode spec dict."""
    return nsx.api_post(opts, PATH, body=body, profile=profile)


def update(opts, node_id, body, profile=None):
    """Update an existing edge transport node."""
    return nsx.api_put(opts, f"{PATH}/{node_id}", body=body, profile=profile)


def delete(opts, node_id, profile=None):
    """Delete an edge transport node."""
    return nsx.api_delete(opts, f"{PATH}/{node_id}", profile=profile)


def redeploy(opts, node_id, body=None, profile=None):
    """Redeploy an edge transport node (POST with ``?action=redeploy``)."""
    return nsx.api_post(opts, f"{PATH}/{node_id}?action=redeploy", body=body, profile=profile)


def state(opts, node_id, profile=None):
    """Return the realization state of the edge transport node."""
    return nsx.api_get(opts, f"{PATH}/{node_id}/state", profile=profile)


def cluster_allocation_status(opts, cluster_id, profile=None):
    """Return allocation status for edge nodes in *cluster_id*."""
    return nsx.api_get(
        opts, f"{EDGE_CLUSTERS_PATH}/{cluster_id}/allocation-status", profile=profile
    )
