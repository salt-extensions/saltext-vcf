"""Client for a vCenter cluster's root resource pool via SOAP/pyVmomi.

Every cluster has an implicit root ``ResourcePool``
(``ClusterComputeResource.resourcePool``). This wraps
:mod:`vim_resource_pool`'s share-level config for that pool, resolved by
cluster name/moId instead of the resource pool's own name/moId.
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


def root_resource_pool(opts, cluster, profile=None):
    """Return the moId of *cluster*'s root resource pool."""
    return _cluster(opts, cluster, profile=profile).resourcePool._moId  # noqa: SLF001


def get_shares(opts, cluster, profile=None):
    """Return ``{cpu, memory}`` allocation for *cluster*'s root resource pool."""
    rp_id = root_resource_pool(opts, cluster, profile=profile)
    return rp_c.get_shares(opts, rp_id, profile=profile)


def set_shares(opts, cluster, *, cpu=None, memory=None, profile=None):
    """Set CPU and/or memory allocation on *cluster*'s root resource pool."""
    rp_id = root_resource_pool(opts, cluster, profile=profile)
    return rp_c.set_shares(opts, rp_id, cpu=cpu, memory=memory, profile=profile)
