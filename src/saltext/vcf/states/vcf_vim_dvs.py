"""State module for VDS + DPG.

Notes on NIC teaming / physical-failover mode:

* :py:func:`teaming_configured` sets the uplink-teaming policy on a
  distributed port group (load balancing or explicit failover order).
* LACP-with-LAG on a DVS (LAG create + ``ReconfigureLacp_Task`` on the
  parent DVS, plus per-DPG ``VMwareDvsLagVlanConfig`` binding) is a
  follow-up — this state ships the common non-LAG cases.
"""

from saltext.vcf.clients import vim_dvs as dvs_c
from saltext.vcf.clients import vim_dvs_portgroup as pg_c

__virtualname__ = "vcf_vim_dvs"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, datacenter, num_uplinks=4, max_mtu=1500, description="", profile=None):
    """Ensure VDS *name* exists in *datacenter* with the given config."""
    ret = _ret(name)
    existing = dvs_c.get_or_none(__opts__, name, profile=profile)
    if existing is not None:
        drift = {}
        if existing["max_mtu"] != int(max_mtu):
            drift["max_mtu"] = (existing["max_mtu"], int(max_mtu))
        if not drift:
            ret["comment"] = f"VDS {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"VDS {name} would be updated: {sorted(drift)}"
            return ret
        dvs_c.reconfigure(
            __opts__, name, max_mtu=int(max_mtu), description=description, profile=profile
        )
        ret["changes"] = drift
        ret["comment"] = f"VDS {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VDS {name} would be created in {datacenter}"
        return ret
    dvs_c.create(
        __opts__,
        name,
        datacenter,
        num_uplinks=int(num_uplinks),
        max_mtu=int(max_mtu),
        description=description,
        profile=profile,
    )
    ret["changes"] = {"new": name}
    ret["comment"] = f"VDS {name} created in {datacenter}"
    return ret


def absent(name, profile=None):
    """Ensure VDS *name* does not exist."""
    ret = _ret(name)
    if dvs_c.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"VDS {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VDS {name} would be deleted"
        return ret
    dvs_c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"VDS {name} deleted"
    return ret


def portgroup_present(
    name,
    dvs,
    vlan_id=0,
    num_ports=8,
    binding="earlyBinding",
    promiscuous=False,
    profile=None,
):
    """Ensure a VLAN-backed DPG *name* exists on *dvs*."""
    ret = _ret(name)
    existing = pg_c.get_or_none(__opts__, dvs, name, profile=profile)
    if existing is not None:
        drift = {}
        current_vlan = (existing.get("vlan") or {}).get("vlan_id")
        if current_vlan is not None and current_vlan != int(vlan_id):
            drift["vlan_id"] = (current_vlan, int(vlan_id))
        if existing.get("num_ports") != int(num_ports):
            drift["num_ports"] = (existing.get("num_ports"), int(num_ports))
        if not drift:
            ret["comment"] = f"DPG {name} on {dvs} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"DPG {name} on {dvs} would be updated: {sorted(drift)}"
            return ret
        pg_c.reconfigure(
            __opts__,
            dvs,
            name,
            vlan_id=int(vlan_id),
            num_ports=int(num_ports),
            promiscuous=promiscuous,
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"DPG {name} on {dvs} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DPG {name} would be created on {dvs}"
        return ret
    pg_c.create_vlan(
        __opts__,
        dvs,
        name,
        vlan_id=int(vlan_id),
        num_ports=int(num_ports),
        binding=binding,
        promiscuous=promiscuous,
        profile=profile,
    )
    ret["changes"] = {"new": name}
    ret["comment"] = f"DPG {name} created on {dvs}"
    return ret


def portgroup_absent(name, dvs, profile=None):
    """Ensure DPG *name* on *dvs* does not exist."""
    ret = _ret(name)
    if pg_c.get_or_none(__opts__, dvs, name, profile=profile) is None:
        ret["comment"] = f"DPG {name} on {dvs} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DPG {name} on {dvs} would be deleted"
        return ret
    pg_c.delete(__opts__, dvs, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"DPG {name} on {dvs} deleted"
    return ret


def teaming_configured(
    name,
    dvs,
    policy,
    reverse_policy=None,
    notify_switches=None,
    rolling_order=None,
    check_beacon=None,
    active_uplinks=None,
    standby_uplinks=None,
    profile=None,
):
    """Ensure DPG *name* on *dvs* uses the given uplink-teaming policy.

    Satisfies the "virtual switches must be set up in a physical network
    failover mode (LACP, teaming)" requirement for distributed port
    groups. LACP-with-LAG (LAG creation + ``ReconfigureLacp_Task`` on
    the parent DVS) is a follow-up; this state covers the common
    load-balance / failover-explicit cases.

    Only fields the caller passes (non-``None``) are diffed; fields left
    as ``None`` are treated as "don't manage".
    """
    ret = _ret(name)
    existing = pg_c.get_or_none(__opts__, dvs, name, profile=profile)
    if existing is None:
        ret["result"] = False
        ret["comment"] = f"DPG {name} not found on {dvs}"
        return ret
    current = existing.get("teaming") or {}
    desired = {
        "policy": policy,
        "reverse_policy": reverse_policy,
        "notify_switches": notify_switches,
        "rolling_order": rolling_order,
        "check_beacon": check_beacon,
        "active_uplinks": list(active_uplinks) if active_uplinks is not None else None,
        "standby_uplinks": list(standby_uplinks) if standby_uplinks is not None else None,
    }
    drift = {}
    for k, want in desired.items():
        if want is None:
            continue
        have = current.get(k)
        if k in ("active_uplinks", "standby_uplinks"):
            have = list(have or [])
        if have != want:
            drift[k] = (have, want)
    if not drift:
        ret["comment"] = f"DPG {name} teaming on {dvs} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DPG {name} teaming on {dvs} would be updated: {sorted(drift)}"
        return ret
    pg_c.set_teaming(
        __opts__,
        dvs,
        name,
        policy=policy,
        reverse_policy=reverse_policy,
        notify_switches=notify_switches,
        rolling_order=rolling_order,
        check_beacon=check_beacon,
        active_uplinks=active_uplinks,
        standby_uplinks=standby_uplinks,
        profile=profile,
    )
    ret["changes"] = drift
    ret["comment"] = f"DPG {name} teaming on {dvs} updated"
    return ret
