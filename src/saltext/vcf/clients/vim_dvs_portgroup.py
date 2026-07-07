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
    return {
        "moid": pg._moId,  # noqa: SLF001
        "key": pg.key,
        "name": pg.name,
        "num_ports": cfg.numPorts,
        "type": str(cfg.type),
        "binding": str(cfg.portBinding) if hasattr(cfg, "portBinding") else None,
        "vlan": vlan_info,
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
