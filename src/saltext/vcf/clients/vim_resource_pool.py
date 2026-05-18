"""SOAP ops on resource pools: move + share-level config.

REST ``/api/vcenter/resource-pool`` lacks both move and the share-level
``cpuAllocation``/``memoryAllocation`` config. These go through pyVmomi
``vim.ResourcePool``.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _find_rp(opts, rp_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.ResourcePool], True
    )
    try:
        for rp in container.view:
            if rp_id_or_name in (rp._moId, rp.name):  # noqa: SLF001
                return rp
    finally:
        container.Destroy()
    raise LookupError(f"resource pool {rp_id_or_name!r} not found")


def move(opts, rp_id_or_name, target_parent, profile=None):
    """Move *rp_id_or_name* under *target_parent*. Synchronous.

    *target_parent* may be a resource-pool moId, name, or ``vim.ResourcePool``.
    """
    rp = _find_rp(opts, rp_id_or_name, profile=profile)
    target = (
        target_parent
        if isinstance(target_parent, vim.ResourcePool)
        else _find_rp(opts, target_parent, profile=profile)
    )
    target.MoveIntoResourcePool(list=[rp])
    return {"resource_pool": rp._moId, "new_parent": target._moId}  # noqa: SLF001


def _allocation(info):
    return {
        "reservation": int(info.reservation or 0),
        "expandable_reservation": bool(info.expandableReservation),
        "limit": int(info.limit if info.limit is not None else -1),
        "shares_level": str(info.shares.level) if info.shares else None,
        "shares_value": int(info.shares.shares) if info.shares else None,
    }


def get_shares(opts, rp_id_or_name, profile=None):
    """Return ``{cpu, memory}`` allocation dicts (reservation, limit, shares)."""
    rp = _find_rp(opts, rp_id_or_name, profile=profile)
    cfg = rp.config
    return {"cpu": _allocation(cfg.cpuAllocation), "memory": _allocation(cfg.memoryAllocation)}


def _merge_allocation(current, spec):
    """Merge *spec* (incoming overrides) on top of *current* (existing allocation info)."""
    info = vim.ResourceAllocationInfo()
    info.reservation = int(spec.get("reservation", current.reservation or 0))
    info.expandableReservation = bool(
        spec.get("expandable_reservation", current.expandableReservation)
    )
    info.limit = int(spec.get("limit", current.limit if current.limit is not None else -1))
    shares = vim.SharesInfo()
    shares.level = spec.get("shares_level", current.shares.level if current.shares else "normal")
    shares.shares = int(spec.get("shares_value", current.shares.shares if current.shares else 4000))
    info.shares = shares
    return info


def set_shares(opts, rp_id_or_name, *, cpu=None, memory=None, profile=None):
    """Set CPU and/or memory allocation. Each is a dict with any of:
    ``reservation``, ``expandable_reservation``, ``limit``,
    ``shares_level`` (``low|normal|high|custom``), ``shares_value`` (int).

    SOAP ``ResourceConfigSpec`` requires both ``cpuAllocation`` and
    ``memoryAllocation`` to be populated; any None argument is merged on top
    of the pool's current allocation so partial updates work safely.
    """
    rp = _find_rp(opts, rp_id_or_name, profile=profile)
    cfg = rp.config
    config = vim.ResourceConfigSpec()
    config.cpuAllocation = _merge_allocation(cfg.cpuAllocation, cpu or {})
    config.memoryAllocation = _merge_allocation(cfg.memoryAllocation, memory or {})
    rp.UpdateConfig(name=rp.name, config=config)
    return get_shares(opts, rp_id_or_name, profile=profile)
