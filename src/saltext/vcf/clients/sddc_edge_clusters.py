"""SDDC Manager edge cluster lifecycle (/v1/edge-clusters).

Distinct from NSX direct edge-cluster management (``nsx_edge_cluster``):
SDDC Manager orchestrates the deployment of NSX Edge VMs as part of a
workload domain. Use this surface when you want SDDC to lay down edges
for you; use the NSX surface for read-after-deploy queries.
"""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/edge-clusters"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, cluster_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{cluster_id}", profile=profile)


def get_or_none(opts, cluster_id, profile=None):
    try:
        return get(opts, cluster_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def validate(opts, spec, profile=None):
    """Validate an edge cluster spec before deployment."""
    return sddc.api_post(opts, "/v1/edge-cluster-validations", body=spec, profile=profile)


def create(opts, spec, profile=None):
    """Deploy an NSX edge cluster via SDDC Manager. Returns the task body."""
    return sddc.api_post(opts, PATH, body=spec, profile=profile)


def expand(opts, cluster_id, spec, profile=None):
    """Add edge VMs to *cluster_id*."""
    return sddc.api_patch(opts, f"{PATH}/{cluster_id}", body=spec, profile=profile)


def delete(opts, cluster_id, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{cluster_id}", profile=profile)
