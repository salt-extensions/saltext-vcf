"""State module for standard vSwitch / port group / VMkernel adapters.

Note on NIC teaming / physical-failover mode:

* :py:func:`vswitch_teaming_configured` covers the four load-balancing
  policies plus explicit-failover order on a standard vSwitch.
* LACP is DVS-only in vSphere — it is not available on a standard
  vSwitch. See :py:mod:`saltext.vcf.states.vcf_vim_dvs` for the DPG
  equivalent; LACP-with-LAG (LAG creation +
  ``ReconfigureLacp_Task`` on the DVS) is a follow-up.
"""

from saltext.vcf.clients import vim_host_network as c

__virtualname__ = "vcf_vim_host_network"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def vswitch_present(
    name,
    host,
    num_ports=None,
    mtu=1500,
    pnic_devices=None,
    profile=None,
):
    """Ensure a standard vSwitch *name* exists on *host* with the given config.

    *num_ports* is a create-time hint only — ESXi 5+ auto-scales the
    port count internally, so passing a fixed value produces spurious
    drift on every apply.  Omit it to skip the drift check; the
    *creation* of a new vSwitch still falls back to 128.
    """
    ret = _ret(name)
    existing = c.vswitch_get_or_none(__opts__, host, name, profile=profile)
    desired_pnics = sorted(pnic_devices or [])
    if existing is not None:
        drift = {}
        if existing["mtu"] != int(mtu):
            drift["mtu"] = (existing["mtu"], int(mtu))
        if num_ports is not None and existing["num_ports"] != int(num_ports):
            drift["num_ports"] = (existing["num_ports"], int(num_ports))
        if sorted(existing.get("pnic_devices") or []) != desired_pnics:
            drift["pnic_devices"] = (existing.get("pnic_devices"), desired_pnics)
        if not drift:
            ret["comment"] = f"vSwitch {name} on {host} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"vSwitch {name} on {host} would be updated: {sorted(drift)}"
            return ret
        c.vswitch_update(
            __opts__,
            host,
            name,
            num_ports=int(num_ports) if num_ports is not None else existing["num_ports"],
            mtu=int(mtu),
            pnic_devices=desired_pnics or None,
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"vSwitch {name} on {host} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vSwitch {name} would be created on {host}"
        return ret
    c.vswitch_add(
        __opts__,
        host,
        name,
        num_ports=int(num_ports) if num_ports is not None else 128,
        mtu=int(mtu),
        pnic_devices=desired_pnics or None,
        profile=profile,
    )
    ret["changes"] = {"new": name}
    ret["comment"] = f"vSwitch {name} created on {host}"
    return ret


def vswitch_absent(name, host, profile=None):
    ret = _ret(name)
    if c.vswitch_get_or_none(__opts__, host, name, profile=profile) is None:
        ret["comment"] = f"vSwitch {name} on {host} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vSwitch {name} on {host} would be deleted"
        return ret
    c.vswitch_remove(__opts__, host, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"vSwitch {name} on {host} deleted"
    return ret


def portgroup_present(
    name,
    host,
    vswitch,
    vlan_id=0,
    promiscuous=None,
    mac_changes=None,
    forged_transmits=None,
    profile=None,
):
    """Ensure a standard port group *name* exists with the given config.

    Security-policy args (``promiscuous`` / ``mac_changes`` /
    ``forged_transmits``): ``True`` accepts, ``False`` rejects, ``None``
    (default) inherits the vSwitch policy.

    Nested-VM labs typically want all three ``True`` on the port group
    carrying nested workloads so nested MAC addresses can traverse the
    physical vSwitch.
    """
    ret = _ret(name)
    existing = c.portgroup_get_or_none(__opts__, host, name, profile=profile)
    desired_sec = {
        "promiscuous": promiscuous,
        "mac_changes": mac_changes,
        "forged_transmits": forged_transmits,
    }
    if existing is not None:
        drift = {}
        if existing["vlan_id"] != int(vlan_id):
            drift["vlan_id"] = (existing["vlan_id"], int(vlan_id))
        if existing["vswitch"] != vswitch:
            drift["vswitch"] = (existing["vswitch"], vswitch)
        for k, want in desired_sec.items():
            have = existing.get("security", {}).get(k)
            if want is not None and have != want:
                drift[f"security.{k}"] = (have, want)
        if not drift:
            ret["comment"] = f"port group {name} on {host} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"port group {name} on {host} would be updated: {sorted(drift)}"
            return ret
        c.portgroup_update(
            __opts__,
            host,
            name,
            vlan_id=int(vlan_id),
            vswitch=vswitch,
            **desired_sec,
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"port group {name} on {host} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"port group {name} would be created on {host}"
        return ret
    c.portgroup_add(
        __opts__,
        host,
        name,
        vswitch,
        vlan_id=int(vlan_id),
        **desired_sec,
        profile=profile,
    )
    ret["changes"] = {"new": name}
    ret["comment"] = f"port group {name} created on {host}"
    return ret


def portgroup_absent(name, host, profile=None):
    ret = _ret(name)
    if c.portgroup_get_or_none(__opts__, host, name, profile=profile) is None:
        ret["comment"] = f"port group {name} on {host} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"port group {name} on {host} would be deleted"
        return ret
    c.portgroup_remove(__opts__, host, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"port group {name} on {host} deleted"
    return ret


def vmkernel_present(
    name,
    host,
    portgroup=None,
    dhcp=False,
    ip_address=None,
    subnet_mask=None,
    mtu=1500,
    profile=None,
):
    """Ensure a VMkernel *name* (device id, e.g. ``vmk1``) exists.

    If the device doesn't exist, a *portgroup* is required to bind it to.
    For an existing vmkernel, drift on IP/MTU/DHCP triggers an update.
    """
    ret = _ret(name)
    existing = c.vmkernel_get_or_none(__opts__, host, name, profile=profile)
    if existing is not None:
        drift = {}
        if bool(existing["dhcp"]) != bool(dhcp):
            drift["dhcp"] = (existing["dhcp"], dhcp)
        if not dhcp:
            if ip_address is not None and existing["ip_address"] != ip_address:
                drift["ip_address"] = (existing["ip_address"], ip_address)
            if subnet_mask is not None and existing["subnet_mask"] != subnet_mask:
                drift["subnet_mask"] = (existing["subnet_mask"], subnet_mask)
        if mtu is not None and existing["mtu"] != int(mtu):
            drift["mtu"] = (existing["mtu"], int(mtu))
        if not drift:
            ret["comment"] = f"vmkernel {name} on {host} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"vmkernel {name} on {host} would be updated: {sorted(drift)}"
            return ret
        c.vmkernel_update(
            __opts__,
            host,
            name,
            dhcp=dhcp,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            mtu=mtu,
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"vmkernel {name} on {host} updated"
        return ret
    if portgroup is None:
        ret["result"] = False
        ret["comment"] = f"vmkernel {name} missing on {host}; provide portgroup= to create"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vmkernel would be created on {host} portgroup={portgroup}"
        return ret
    device = c.vmkernel_add(
        __opts__,
        host,
        portgroup,
        dhcp=dhcp,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        mtu=mtu,
        profile=profile,
    )
    ret["changes"] = {"new": device}
    ret["comment"] = f"vmkernel {device} created on {host}"
    return ret


def vmkernel_absent(name, host, profile=None):
    ret = _ret(name)
    if c.vmkernel_get_or_none(__opts__, host, name, profile=profile) is None:
        ret["comment"] = f"vmkernel {name} on {host} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vmkernel {name} on {host} would be deleted"
        return ret
    c.vmkernel_remove(__opts__, host, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"vmkernel {name} on {host} deleted"
    return ret


def vswitch_teaming_configured(
    name,
    host,
    policy,
    reverse_policy=None,
    notify_switches=None,
    rolling_order=None,
    check_beacon=None,
    active_nic=None,
    standby_nic=None,
    profile=None,
):
    """Ensure standard vSwitch *name* on *host* uses the given NIC-teaming policy.

    Satisfies the "virtual switches must be set up in a physical network
    failover mode (LACP, teaming)" requirement for standard vSwitches.
    LACP itself is DVS-only in vSphere; on a standard vSwitch the
    ``policy`` value covers all four load-balancing modes and explicit
    failover order.

    Only fields the caller passes (non-``None``) are considered for drift;
    ``None`` means "don't manage this field", so callers can pin just the
    policy while leaving everything else as ESXi sees it.
    """
    ret = _ret(name)
    existing = c.vswitch_get_or_none(__opts__, host, name, profile=profile)
    if existing is None:
        ret["result"] = False
        ret["comment"] = f"vSwitch {name} not found on {host}"
        return ret
    current = existing.get("teaming") or {}
    desired = {
        "policy": policy,
        "reverse_policy": reverse_policy,
        "notify_switches": notify_switches,
        "rolling_order": rolling_order,
        "check_beacon": check_beacon,
        "active_nic": list(active_nic) if active_nic is not None else None,
        "standby_nic": list(standby_nic) if standby_nic is not None else None,
    }
    drift = {}
    for k, want in desired.items():
        if want is None:
            continue
        have = current.get(k)
        if k in ("active_nic", "standby_nic"):
            have = list(have or [])
        if have != want:
            drift[k] = (have, want)
    if not drift:
        ret["comment"] = f"vSwitch {name} teaming on {host} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vSwitch {name} teaming on {host} would be updated: {sorted(drift)}"
        return ret
    c.vswitch_set_teaming(
        __opts__,
        host,
        name,
        policy=policy,
        reverse_policy=reverse_policy,
        notify_switches=notify_switches,
        rolling_order=rolling_order,
        check_beacon=check_beacon,
        active_nic=active_nic,
        standby_nic=standby_nic,
        profile=profile,
    )
    ret["changes"] = drift
    ret["comment"] = f"vSwitch {name} teaming on {host} updated"
    return ret
