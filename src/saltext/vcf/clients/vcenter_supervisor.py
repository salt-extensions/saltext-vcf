"""vCenter Supervisor / VKS (vSphere Kubernetes Service).

The Supervisor cluster overlays Kubernetes onto a vSphere cluster — workloads
(VMs, containers, TKG clusters) run as Kubernetes resources.

Endpoints under ``/api/vcenter/namespace-management/*``.
"""

import requests

from saltext.vcf.utils import vcenter

CLUSTERS = "/api/vcenter/namespace-management/clusters"
COMPAT = "/api/vcenter/namespace-management/cluster-compatibility"
NAMESPACES = "/api/vcenter/namespaces/instances"


def list_clusters(opts, profile=None):
    """List Supervisor-enabled clusters."""
    return vcenter.api_get(opts, CLUSTERS, profile=profile)


def get_cluster(opts, cluster_id, profile=None):
    return vcenter.api_get(opts, f"{CLUSTERS}/{cluster_id}", profile=profile)


def get_cluster_or_none(opts, cluster_id, profile=None):
    try:
        return get_cluster(opts, cluster_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_compatibility(opts, profile=None):
    """List all vSphere clusters with their Supervisor compatibility status."""
    return vcenter.api_get(opts, COMPAT, profile=profile)


def enable_cluster(opts, cluster_id, enable_spec, profile=None):
    """Enable Supervisor on a vSphere cluster.

    *enable_spec* is the EnableSpec dict per the vSphere REST API — networking,
    master sizing, content library, etc.
    """
    return vcenter.api_post(opts, f"{CLUSTERS}/{cluster_id}", body=enable_spec, profile=profile)


def disable_cluster(opts, cluster_id, profile=None):
    return vcenter.api_delete(opts, f"{CLUSTERS}/{cluster_id}", profile=profile)


def list_namespaces(opts, profile=None):
    """List vSphere namespaces (across all Supervisor clusters)."""
    return vcenter.api_get(opts, NAMESPACES, profile=profile)


def get_namespace(opts, namespace_id, profile=None):
    return vcenter.api_get(opts, f"{NAMESPACES}/{namespace_id}", profile=profile)


def get_namespace_or_none(opts, namespace_id, profile=None):
    try:
        return get_namespace(opts, namespace_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_namespace(opts, namespace_spec, profile=None):
    """Create a vSphere namespace (Kubernetes namespace in the Supervisor)."""
    return vcenter.api_post(opts, NAMESPACES, body=namespace_spec, profile=profile)


def delete_namespace(opts, namespace_id, profile=None):
    return vcenter.api_delete(opts, f"{NAMESPACES}/{namespace_id}", profile=profile)
