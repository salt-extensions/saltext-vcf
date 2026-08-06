"""Client for named child resource pools under a vCenter cluster (SOAP/pyVmomi).

Every cluster has an implicit root ``ResourcePool``
(``ClusterComputeResource.resourcePool``) -- but vCenter rejects *any*
field (reservation, limit, **or** shares) being set on that root pool with
``com.vmware.vim.resourcePool.error.rootSettingDisallowed``, since shares
are only meaningful relative to sibling pools and the root has none.

The real capability this wraps (matching the Ansible role's own
``community.vmware.vmware_resource_pool``) is a *named* child pool created
directly under the cluster's root -- which is a completely ordinary,
fully-configurable ``vim.ResourcePool`` once it exists.
"""

from pyVmomi import vim

from saltext.vcf.clients import vim_resource_pool as rp_c
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


def _find_child_pool(cluster_obj, name):
    for rp in cluster_obj.resourcePool.resourcePool:
        if rp.name == name:
            return rp
    return None


def get_or_none(opts, cluster, name, profile=None):
    """Return the moId of resource pool *name* under *cluster*, or ``None``."""
    cluster_obj = _cluster(opts, cluster, profile=profile)
    rp = _find_child_pool(cluster_obj, name)
    return rp._moId if rp else None  # noqa: SLF001


def create(opts, cluster, name, profile=None):
    """Create resource pool *name* directly under *cluster*'s root pool.

    Returns the new pool's moId. ``CreateResourcePool`` requires a full
    ``ResourceConfigSpec`` up front (unlike ``UpdateConfig``, there's no
    existing config to leave fields unset against) -- created with
    vSphere's own defaults (normal shares, no reservation, no limit).
    """
    cluster_obj = _cluster(opts, cluster, profile=profile)
    default_alloc = vim.ResourceAllocationInfo(
        reservation=0,
        expandableReservation=True,
        limit=-1,
        shares=vim.SharesInfo(level="normal"),
    )
    spec = vim.ResourceConfigSpec(cpuAllocation=default_alloc, memoryAllocation=default_alloc)
    new_rp = cluster_obj.resourcePool.CreateResourcePool(name=name, spec=spec)
    return new_rp._moId  # noqa: SLF001


def delete(opts, cluster, name, profile=None):
    """Delete resource pool *name* under *cluster*."""
    cluster_obj = _cluster(opts, cluster, profile=profile)
    rp = _find_child_pool(cluster_obj, name)
    if rp is None:
        raise LookupError(f"resource pool {name!r} not found under cluster {cluster!r}")
    task = rp.Destroy_Task()
    soap.wait_for_task(task)


def get_shares(opts, cluster, name, profile=None):
    """Return ``{cpu, memory}`` allocation for resource pool *name* under *cluster*."""
    rp_id = get_or_none(opts, cluster, name, profile=profile)
    if rp_id is None:
        raise LookupError(f"resource pool {name!r} not found under cluster {cluster!r}")
    return rp_c.get_shares(opts, rp_id, profile=profile)


def set_shares(opts, cluster, name, *, cpu=None, memory=None, profile=None):
    """Set CPU and/or memory allocation on resource pool *name* under *cluster*."""
    rp_id = get_or_none(opts, cluster, name, profile=profile)
    if rp_id is None:
        raise LookupError(f"resource pool {name!r} not found under cluster {cluster!r}")
    return rp_c.set_shares(opts, rp_id, cpu=cpu, memory=memory, profile=profile)
