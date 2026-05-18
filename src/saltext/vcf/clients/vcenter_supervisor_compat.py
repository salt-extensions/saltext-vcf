"""Supervisor compatibility probes — DVS, edge cluster, cluster sizing.

Pre-enablement helpers used by an operator before turning Supervisor on
a vSphere cluster. All endpoints accept ``cluster=`` (and sometimes
``distributed_switch=``) as query parameters.
"""

from saltext.vcf.utils import vcenter

CLUSTER_COMPAT = "/api/vcenter/namespace-management/cluster-compatibility"
DVS_COMPAT = "/api/vcenter/namespace-management/distributed-switch-compatibility"
EDGE_COMPAT = "/api/vcenter/namespace-management/edge-cluster-compatibility"
SIZE_INFO = "/api/vcenter/namespace-management/cluster-size-info"


def list_cluster_compatibility(opts, profile=None):
    """List Supervisor compatibility for every vSphere cluster."""
    return vcenter.api_get(opts, CLUSTER_COMPAT, profile=profile)


def list_dvs_compatibility(opts, cluster_id, profile=None):
    """List Supervisor compatibility per VDS in *cluster_id*."""
    return vcenter.api_get(opts, DVS_COMPAT, params={"cluster": cluster_id}, profile=profile)


def list_edge_cluster_compatibility(opts, cluster_id, distributed_switch, profile=None):
    """List Supervisor compatibility per NSX edge cluster bound to *distributed_switch*."""
    return vcenter.api_get(
        opts,
        EDGE_COMPAT,
        params={"cluster": cluster_id, "distributed_switch": distributed_switch},
        profile=profile,
    )


def get_cluster_size_info(opts, profile=None):
    """Return the predefined Supervisor sizing options (TINY/SMALL/MEDIUM/LARGE)."""
    return vcenter.api_get(opts, SIZE_INFO, profile=profile)
