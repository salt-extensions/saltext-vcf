"""State module for VDS + DPG."""

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
