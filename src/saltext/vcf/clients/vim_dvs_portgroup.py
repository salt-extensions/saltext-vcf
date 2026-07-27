"""Distributed Port Group (DPG) lifecycle via SOAP.

DPG identity:

- ``key`` (server-assigned, stable, used by VM NIC backings)
- ``name`` (human-readable; we use it as the lookup key)
- ``portgroupKey`` returned in :py:func:`saltext.vcf.clients.vim_vm_nic.list_`
  is this same ``key``.

Two creation paths:

- :py:func:`create_vlan` for VLAN-backed (standard / trunk / private)
- :py:func:`create_overlay` for overlay-backed (early-binding ephemeral
  for use under NSX/Avi)

NIC teaming / physical-uplink failover mode: :py:func:`get_teaming` and
:py:func:`set_teaming` cover the load-balancing / explicit-failover
policies on the DPG's default port config.

LACP-with-LAG is a follow-up: it requires LAG creation and
``ReconfigureLacp_Task`` on the parent DVS (see
:py:mod:`saltext.vcf.clients.vim_dvs`) plus per-DPG
``VMwareDvsLagVlanConfig`` binding via ``UplinkPortOrderPolicy``.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _dvs(opts, name_or_id, profile=None):
    from saltext.vcf.clients.vim_dvs import _dvs as resolve

    return resolve(opts, name_or_id, profile=profile)


def _dpg(opts, dvs_name_or_id, name, profile=None):
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    for pg in dvs.portgroup or []:
        if name in (pg._moId, pg.name, pg.key):  # noqa: SLF001
            return pg
    raise LookupError(f"port group {name!r} not found on DVS {dvs.name!r}")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def list_(opts, dvs_name_or_id, profile=None):
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    return [_to_dict(pg) for pg in (dvs.portgroup or [])]


def get(opts, dvs_name_or_id, name, profile=None):
    return _to_dict(_dpg(opts, dvs_name_or_id, name, profile=profile))


def get_or_none(opts, dvs_name_or_id, name, profile=None):
    try:
        return get(opts, dvs_name_or_id, name, profile=profile)
    except LookupError:
        return None


def _to_dict(pg):
    cfg = pg.config
    vlan_info = None
    if cfg.defaultPortConfig and cfg.defaultPortConfig.vlan:
        v = cfg.defaultPortConfig.vlan
        if isinstance(v, vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec):
            vlan_info = {"kind": "vlan", "vlan_id": int(v.vlanId)}
        elif isinstance(v, vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
            vlan_info = {
                "kind": "trunk",
                "ranges": [{"start": r.start, "end": r.end} for r in (v.vlanId or [])],
            }
        elif isinstance(v, vim.dvs.VmwareDistributedVirtualSwitch.PvlanSpec):
            vlan_info = {"kind": "pvlan", "primary_vlan_id": int(v.pvlanId)}
    teaming_info = None
    if cfg.defaultPortConfig is not None:
        teaming_info = _teaming_to_dict(getattr(cfg.defaultPortConfig, "uplinkTeamingPolicy", None))
    return {
        "moid": pg._moId,  # noqa: SLF001
        "key": pg.key,
        "name": pg.name,
        "num_ports": cfg.numPorts,
        "type": str(cfg.type),
        "binding": str(cfg.portBinding) if hasattr(cfg, "portBinding") else None,
        "vlan": vlan_info,
        "teaming": teaming_info,
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_vlan(
    opts,
    dvs_name_or_id,
    name,
    *,
    vlan_id=0,
    num_ports=8,
    binding="earlyBinding",
    auto_expand=True,
    promiscuous=False,
    profile=None,
):
    """Create a VLAN-backed DPG.

    *vlan_id* of 0 means the DPG is untagged. Use :py:func:`create_trunk`
    for a trunk port group.
    """
    spec = _vlan_spec(name, vlan_id, num_ports, binding, auto_expand, promiscuous)
    return _add(opts, dvs_name_or_id, spec, profile=profile)


def create_trunk(
    opts,
    dvs_name_or_id,
    name,
    *,
    vlan_ranges,
    num_ports=8,
    binding="earlyBinding",
    profile=None,
):
    """Create a VLAN-trunk-backed DPG. *vlan_ranges* is a list of ``(start, end)`` tuples."""
    ranges = [vim.NumericRange(start=int(s), end=int(e)) for s, e in vlan_ranges]
    trunk = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec(vlanId=ranges)
    port_cfg = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy(vlan=trunk)
    spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec(
        name=name,
        numPorts=int(num_ports),
        type=binding,
        defaultPortConfig=port_cfg,
    )
    return _add(opts, dvs_name_or_id, spec, profile=profile)


def _vlan_spec(name, vlan_id, num_ports, binding, auto_expand, promiscuous):
    vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec(vlanId=int(vlan_id))
    sec = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy(
        allowPromiscuous=vim.BoolPolicy(value=bool(promiscuous)),
    )
    port_cfg = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy(
        vlan=vlan, securityPolicy=sec
    )
    return vim.dvs.DistributedVirtualPortgroup.ConfigSpec(
        name=name,
        numPorts=int(num_ports),
        type=binding,
        autoExpand=bool(auto_expand),
        defaultPortConfig=port_cfg,
    )


def _add(opts, dvs_name_or_id, spec, profile=None):
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    task = dvs.AddDVPortgroup_Task(spec=[spec])
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Reconfigure / Delete
# ---------------------------------------------------------------------------


def reconfigure(
    opts,
    dvs_name_or_id,
    name,
    *,
    vlan_id=None,
    num_ports=None,
    promiscuous=None,
    profile=None,
):
    """Update DPG config fields. Only non-None fields are applied."""
    pg = _dpg(opts, dvs_name_or_id, name, profile=profile)
    cfg = vim.dvs.DistributedVirtualPortgroup.ConfigSpec(configVersion=pg.config.configVersion)
    if num_ports is not None:
        cfg.numPorts = int(num_ports)
    if vlan_id is not None or promiscuous is not None:
        port_cfg = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
        if vlan_id is not None:
            port_cfg.vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec(vlanId=int(vlan_id))
        if promiscuous is not None:
            port_cfg.securityPolicy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy(
                allowPromiscuous=vim.BoolPolicy(value=bool(promiscuous)),
            )
        cfg.defaultPortConfig = port_cfg
    task = pg.ReconfigureDVPortgroup_Task(spec=cfg)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def delete(opts, dvs_name_or_id, name, profile=None):
    pg = _dpg(opts, dvs_name_or_id, name, profile=profile)
    task = pg.Destroy_Task()
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# NIC teaming / failover policy on a DVS port group
# ---------------------------------------------------------------------------
#
# Physical-uplink failover mode (Requirement: virtual switches must be set up
# in a physical network failover mode — LACP, teaming). This surface covers
# the common teaming policies on a DPG. LACP-with-LAG (LAG creation +
# ``ReconfigureLacp_Task`` on the DVS) is a follow-up; see the module
# docstring.

_DVS_TEAMING_POLICIES = {
    "loadbalance_ip",
    "loadbalance_srcmac",
    "loadbalance_srcid",
    "failover_explicit",
    "loadbalance_loadbased",
}


def _teaming_to_dict(teaming):
    """Return a plain-dict rendering of ``VmwareUplinkPortTeamingPolicy`` (or ``None``)."""
    if teaming is None:
        return None

    def _v(field):
        wrapper = getattr(teaming, field, None)
        return getattr(wrapper, "value", None) if wrapper is not None else None

    order = getattr(teaming, "uplinkPortOrder", None)
    failure = getattr(teaming, "failureCriteria", None)
    return {
        "inherited": getattr(teaming, "inherited", None),
        "policy": _v("policy"),
        "reverse_policy": _v("reversePolicy"),
        "notify_switches": _v("notifySwitches"),
        "rolling_order": _v("rollingOrder"),
        "check_beacon": (
            getattr(getattr(failure, "checkBeacon", None), "value", None) if failure else None
        ),
        "active_uplinks": list(getattr(order, "activeUplinkPort", None) or []) if order else [],
        "standby_uplinks": list(getattr(order, "standbyUplinkPort", None) or []) if order else [],
    }


def _build_uplink_teaming_policy(
    policy,
    *,
    reverse_policy=None,
    notify_switches=None,
    rolling_order=None,
    check_beacon=None,
    active_uplinks=None,
    standby_uplinks=None,
):
    if policy not in _DVS_TEAMING_POLICIES:
        raise ValueError(
            f"teaming policy must be one of {sorted(_DVS_TEAMING_POLICIES)}; got {policy!r}"
        )
    t = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortTeamingPolicy(
        inherited=False,
        policy=vim.StringPolicy(inherited=False, value=policy),
    )
    if reverse_policy is not None:
        t.reversePolicy = vim.BoolPolicy(inherited=False, value=bool(reverse_policy))
    if notify_switches is not None:
        t.notifySwitches = vim.BoolPolicy(inherited=False, value=bool(notify_switches))
    if rolling_order is not None:
        t.rollingOrder = vim.BoolPolicy(inherited=False, value=bool(rolling_order))
    if check_beacon is not None:
        t.failureCriteria = vim.dvs.VmwareDistributedVirtualSwitch.FailureCriteria(
            inherited=False,
            checkBeacon=vim.BoolPolicy(inherited=False, value=bool(check_beacon)),
        )
    if active_uplinks is not None or standby_uplinks is not None:
        t.uplinkPortOrder = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortOrderPolicy(
            inherited=False,
            activeUplinkPort=list(active_uplinks or []),
            standbyUplinkPort=list(standby_uplinks or []),
        )
    return t


def get_teaming(opts, dvs_name_or_id, name, profile=None):
    """Return the current uplink teaming policy for DPG *name* (or ``None``)."""
    pg = _dpg(opts, dvs_name_or_id, name, profile=profile)
    default = pg.config.defaultPortConfig
    if default is None:
        return None
    return _teaming_to_dict(getattr(default, "uplinkTeamingPolicy", None))


def set_teaming(
    opts,
    dvs_name_or_id,
    name,
    *,
    policy,
    reverse_policy=None,
    notify_switches=None,
    rolling_order=None,
    check_beacon=None,
    active_uplinks=None,
    standby_uplinks=None,
    profile=None,
):
    """Set the uplink teaming policy on DPG *name*.

    *policy* is one of ``loadbalance_ip``, ``loadbalance_srcmac``,
    ``loadbalance_srcid``, ``failover_explicit``, ``loadbalance_loadbased``.
    """
    pg = _dpg(opts, dvs_name_or_id, name, profile=profile)
    port_cfg = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy(
        uplinkTeamingPolicy=_build_uplink_teaming_policy(
            policy,
            reverse_policy=reverse_policy,
            notify_switches=notify_switches,
            rolling_order=rolling_order,
            check_beacon=check_beacon,
            active_uplinks=active_uplinks,
            standby_uplinks=standby_uplinks,
        ),
    )
    cfg = vim.dvs.DistributedVirtualPortgroup.ConfigSpec(
        configVersion=pg.config.configVersion,
        defaultPortConfig=port_cfg,
    )
    task = pg.ReconfigureDVPortgroup_Task(spec=cfg)
    soap.wait_for_task(task)
    return get_teaming(opts, dvs_name_or_id, name, profile=profile)
