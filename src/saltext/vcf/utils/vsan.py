"""
vSAN Management SDK (SOAP) connection helpers.

vSAN management uses the ``/vsanHealth`` endpoint on vCenter — a separate
SOAP service from the main vCenter ``/sdk``. Both share authentication;
the vSAN stub re-uses the vCenter session cookie from
:mod:`saltext.vcf.utils.vim`.

The well-known managed-object IDs at ``/vsanHealth`` are stable
(documented in the vSAN Management SDK). Functions here instantiate them
lazily and cache stub+MO pairs per ``(host, username)``.

Used by ``clients/vsan_*`` for cluster vSAN config, disk management,
fault domains, health checks, iSCSI, stretched clusters, and object
inspection.
"""

import ssl

from pyVmomi import vim
from pyVmomi.SoapAdapter import SoapStubAdapter

from saltext.vcf.utils import vim as vim_utils

# Cache vSAN stubs per (host, username). The stub is just a thin wrapper
# around the vCenter session cookie — cheap to re-create but pinning it
# avoids constructing a new ssl context on every call.
_VSAN_STUB_CACHE: dict[str, SoapStubAdapter] = {}


def get_stub(opts, profile=None):
    """Return a vSAN SOAP stub bound to the same session as ``utils.vim``."""
    cfg = vim_utils.get_config(opts, profile=profile)
    key = f"{cfg['host']}:{cfg['username']}"
    cached = _VSAN_STUB_CACHE.get(key)
    if cached is not None:
        return cached

    si = vim_utils.get_service_instance(opts, profile=profile)
    sslContext = (  # noqa: N806  pylint: disable=invalid-name
        None if cfg["verify_ssl"] else ssl._create_unverified_context()
    )
    stub = SoapStubAdapter(
        host=cfg["host"],
        version="vim.version.version10",
        path="/vsanHealth",
        sslContext=sslContext,
    )
    # Re-use vCenter session cookie for SSO
    stub.cookie = si._stub.cookie  # noqa: SLF001
    _VSAN_STUB_CACHE[key] = stub
    return stub


def invalidate_stub(opts, profile=None):
    cfg = vim_utils.get_config(opts, profile=profile)
    _VSAN_STUB_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


# ---------------------------------------------------------------------------
# Managed-object accessors (well-known IDs at /vsanHealth)
# ---------------------------------------------------------------------------


def cluster_config_system(opts, profile=None):
    """vim.cluster.VsanVcClusterConfigSystem — cluster vSAN config CRUD."""
    return vim.cluster.VsanVcClusterConfigSystem(
        "vsan-cluster-config-system", get_stub(opts, profile=profile)
    )


def cluster_health_system(opts, profile=None):
    """vim.cluster.VsanVcClusterHealthSystem — cluster health checks."""
    return vim.cluster.VsanVcClusterHealthSystem(
        "vsan-cluster-health-system", get_stub(opts, profile=profile)
    )


def disk_management_system(opts, profile=None):
    """vim.cluster.VsanVcDiskManagementSystem — disk-group management."""
    return vim.cluster.VsanVcDiskManagementSystem(
        "vsan-disk-management-system", get_stub(opts, profile=profile)
    )


def iscsi_target_system(opts, profile=None):
    """vim.cluster.VsanIscsiTargetSystem — vSAN iSCSI service + targets."""
    return vim.cluster.VsanIscsiTargetSystem(
        "vsan-cluster-iscsi-target-system", get_stub(opts, profile=profile)
    )


def stretched_cluster_system(opts, profile=None):
    """vim.cluster.VsanVcStretchedClusterSystem — stretched-cluster ops."""
    return vim.cluster.VsanVcStretchedClusterSystem(
        "vsan-stretched-cluster-system", get_stub(opts, profile=profile)
    )


def object_system(opts, profile=None):
    """vim.cluster.VsanObjectSystem — vSAN object queries."""
    return vim.cluster.VsanObjectSystem(
        "vsan-cluster-object-system", get_stub(opts, profile=profile)
    )


# ---------------------------------------------------------------------------
# Cluster lookup convenience
# ---------------------------------------------------------------------------


def find_cluster(opts, name_or_id, profile=None):
    """Resolve a cluster by display name or MoId.

    Returns a ``vim.ClusterComputeResource`` or raises ``LookupError``.
    """
    content = vim_utils.content(opts, profile=profile)
    # Try by MoId first (matches the REST surface ids like ``domain-c9``)
    for dc in content.rootFolder.childEntity:
        if not isinstance(dc, vim.Datacenter):
            continue
        for entity in dc.hostFolder.childEntity:
            if not isinstance(entity, vim.ClusterComputeResource):
                continue
            if name_or_id in (entity._moId, entity.name):  # noqa: SLF001
                return entity
    raise LookupError(f"cluster {name_or_id!r} not found")
