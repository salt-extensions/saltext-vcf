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


def _build_allocation(spec):
    """Build a *partial* ``ResourceAllocationInfo`` containing only the
    fields *spec* explicitly names, leaving the rest unset (``None``).

    ``UpdateConfig`` treats an unset field as "leave unchanged" -- critical
    here, because a cluster's root resource pool rejects
    ``reservation``/``limit``/``expandableReservation`` being present in
    the spec *at all* (only ``shares`` is settable there), regardless of
    the value. Always back-filling those fields from the pool's current
    values (the previous behavior) sent them unconditionally and broke
    shares-only updates against the root pool with
    ``vmodl.fault.InvalidArgument`` /
    ``rootSettingDisallowed``.
    """
    info = vim.ResourceAllocationInfo()
    if "reservation" in spec:
        info.reservation = int(spec["reservation"])
    if "expandable_reservation" in spec:
        info.expandableReservation = bool(spec["expandable_reservation"])
    if "limit" in spec:
        info.limit = int(spec["limit"])
    if "shares_level" in spec or "shares_value" in spec:
        shares = vim.SharesInfo()
        if "shares_level" in spec:
            shares.level = spec["shares_level"]
        if "shares_value" in spec:
            shares.shares = int(spec["shares_value"])
        info.shares = shares
    return info


def set_shares(opts, rp_id_or_name, *, cpu=None, memory=None, profile=None):
    """Set CPU and/or memory allocation. Each is a dict with any of:
    ``reservation``, ``expandable_reservation``, ``limit``,
    ``shares_level`` (``low|normal|high|custom``), ``shares_value`` (int).

    SOAP ``ResourceConfigSpec`` requires both ``cpuAllocation`` and
    ``memoryAllocation`` to be present, but only the sub-fields actually
    named in *cpu*/*memory* are populated -- everything else is left unset
    so it's left unchanged server-side, rather than being re-sent with the
    pool's current value (see :func:`_build_allocation`).
    """
    rp = _find_rp(opts, rp_id_or_name, profile=profile)
    config = vim.ResourceConfigSpec()
    config.cpuAllocation = _build_allocation(cpu or {})
    config.memoryAllocation = _build_allocation(memory or {})
    rp.UpdateConfig(name=rp.name, config=config)
    return get_shares(opts, rp_id_or_name, profile=profile)
