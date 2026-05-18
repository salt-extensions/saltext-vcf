"""NSX edge clusters (Management API)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/api/v1/edge-clusters"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, cluster_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{cluster_id}", profile=profile)


def get_or_none(opts, cluster_id, profile=None):
    try:
        return get(opts, cluster_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, body, profile=None):
    """Create an edge cluster. *body* is the EdgeCluster spec dict per NSX API."""
    return nsx.api_post(opts, PATH, body=body, profile=profile)


def update(opts, cluster_id, body, profile=None):
    return nsx.api_put(opts, f"{PATH}/{cluster_id}", body=body, profile=profile)


def delete(opts, cluster_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{cluster_id}", profile=profile)


def state(opts, cluster_id, profile=None):
    """Return realization state of the edge cluster."""
    return nsx.api_get(opts, f"{PATH}/{cluster_id}/state", profile=profile)
