"""Client for cluster-wide DVS Network I/O Control (NIOC).

Applies :mod:`vcenter_dvs_nioc`'s per-switch NIOC toggle across every
Distributed Virtual Switch backing at least one host of a vCenter cluster.
"""

from pyVmomi import vim

from saltext.vcf.clients import vcenter_dvs_nioc as nioc_c
from saltext.vcf.clients import vim_dvs as dvs_c
from saltext.vcf.utils import vim as soap


def _cluster(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if not isinstance(dc, vim.Datacenter):
            continue
        for entity in dc.hostFolder.childEntity:
            if isinstance(entity, vim.ClusterComputeResource) and name_or_id in (
                entity._moId,  # noqa: SLF001
                entity.name,
            ):
                return entity
    raise LookupError(f"cluster {name_or_id!r} not found")


def cluster_dvs_list(opts, cluster, profile=None):
    """Return the moIds of DVS's backing at least one host of *cluster*."""
    cl = _cluster(opts, cluster, profile=profile)
    host_moids = {h._moId for h in (cl.host or [])}  # noqa: SLF001
    return [
        dvs["moid"] for dvs in dvs_c.list_(opts, profile=profile) if host_moids & set(dvs["hosts"])
    ]


def nioc_get(opts, cluster, profile=None):
    """Return ``{dvs_moid: enabled}`` NIOC state for every DVS backing *cluster*."""
    return {
        dvs_moid: nioc_c.nioc_get(opts, dvs_moid, profile=profile)
        for dvs_moid in cluster_dvs_list(opts, cluster, profile=profile)
    }


def nioc_set(opts, cluster, enabled, profile=None):
    """Enable/disable NIOC on every DVS backing *cluster*."""
    for dvs_moid in cluster_dvs_list(opts, cluster, profile=profile):
        nioc_c.nioc_set(opts, dvs_moid, enabled, profile=profile)
