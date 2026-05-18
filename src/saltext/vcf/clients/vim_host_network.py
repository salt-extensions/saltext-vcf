"""Standard vSwitch + port group + VMkernel via SOAP ``HostNetworkSystem``.

Three related surfaces all on ``host.configManager.networkSystem``:

* **vSwitches** — ``AddVirtualSwitch`` / ``UpdateVirtualSwitch`` / ``RemoveVirtualSwitch``
* **Port groups** — ``AddPortGroup`` / ``UpdatePortGroup`` / ``RemovePortGroup``
* **VMkernel adapters** — ``AddVirtualNic`` / ``UpdateVirtualNic`` / ``RemoveVirtualNic``

VMkernel traffic types (``nicType``) include: ``management``, ``vmotion``,
``vsan``, ``faultToleranceLogging``, ``vSphereReplication``, ``provisioning``,
``vSphereProvisioning``, ``vSphereBackupNFC``. Multiple types can be set
on a single vmkernel.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for h in container.view:
            if host_id_or_name in (h._moId, h.name):  # noqa: SLF001
                return h
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


def _net(opts, host, profile=None):
    return _host(opts, host, profile=profile).configManager.networkSystem


# ---------------------------------------------------------------------------
# vSwitches
# ---------------------------------------------------------------------------


def vswitch_list(opts, host, profile=None):
    """List standard vSwitches on *host*."""
    info = _host(opts, host, profile=profile).config.network
    return [_vswitch_to_dict(vs) for vs in (info.vswitch or [])]


def vswitch_get(opts, host, name, profile=None):
    for vs in vswitch_list(opts, host, profile=profile):
        if vs["name"] == name:
            return vs
    raise LookupError(f"vSwitch {name!r} not found on {host!r}")


def vswitch_get_or_none(opts, host, name, profile=None):
    try:
        return vswitch_get(opts, host, name, profile=profile)
    except LookupError:
        return None


def vswitch_add(
    opts,
    host,
    name,
    *,
    num_ports=128,
    mtu=1500,
    pnic_devices=None,
    profile=None,
):
    """Create a standard vSwitch. *pnic_devices* (e.g. ``["vmnic0"]``) attach
    physical uplinks; omit for an internal-only vSwitch."""
    spec = vim.host.VirtualSwitch.Specification(
        numPorts=int(num_ports),
        mtu=int(mtu),
    )
    if pnic_devices:
        bridge = vim.host.VirtualSwitch.BondBridge(
            nicDevice=list(pnic_devices),
        )
        spec.bridge = bridge
    _net(opts, host, profile=profile).AddVirtualSwitch(vswitchName=name, spec=spec)


def vswitch_update(
    opts,
    host,
    name,
    *,
    num_ports=None,
    mtu=None,
    pnic_devices=None,
    profile=None,
):
    """Update a vSwitch. Reads the existing spec, merges non-None fields, writes back."""
    existing = vswitch_get(opts, host, name, profile=profile)
    spec = vim.host.VirtualSwitch.Specification(
        numPorts=int(num_ports) if num_ports is not None else existing["num_ports"],
        mtu=int(mtu) if mtu is not None else existing["mtu"],
    )
    if pnic_devices is not None:
        spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=list(pnic_devices))
    elif existing.get("pnic_devices"):
        spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=existing["pnic_devices"])
    _net(opts, host, profile=profile).UpdateVirtualSwitch(vswitchName=name, spec=spec)


def vswitch_remove(opts, host, name, profile=None):
    _net(opts, host, profile=profile).RemoveVirtualSwitch(vswitchName=name)


def _vswitch_to_dict(vs):
    pnic_devices = []
    if vs.spec and isinstance(vs.spec.bridge, vim.host.VirtualSwitch.BondBridge):
        pnic_devices = list(vs.spec.bridge.nicDevice or [])
    return {
        "name": vs.name,
        "key": vs.key,
        "num_ports": vs.numPorts,
        "num_ports_available": vs.numPortsAvailable,
        "mtu": vs.mtu,
        "pnic_devices": pnic_devices,
        "portgroup_names": [pg.split("-", 1)[-1] for pg in (vs.portgroup or [])],
    }


# ---------------------------------------------------------------------------
# Port groups (standard)
# ---------------------------------------------------------------------------


def portgroup_list(opts, host, profile=None):
    info = _host(opts, host, profile=profile).config.network
    return [_pg_to_dict(pg) for pg in (info.portgroup or [])]


def portgroup_get(opts, host, name, profile=None):
    for pg in portgroup_list(opts, host, profile=profile):
        if pg["name"] == name:
            return pg
    raise LookupError(f"port group {name!r} not found on {host!r}")


def portgroup_get_or_none(opts, host, name, profile=None):
    try:
        return portgroup_get(opts, host, name, profile=profile)
    except LookupError:
        return None


def portgroup_add(opts, host, name, vswitch, *, vlan_id=0, profile=None):
    spec = vim.host.PortGroup.Specification(
        name=name,
        vlanId=int(vlan_id),
        vswitchName=vswitch,
        policy=vim.host.NetworkPolicy(),
    )
    _net(opts, host, profile=profile).AddPortGroup(portgrp=spec)


def portgroup_update(opts, host, name, *, vlan_id=None, vswitch=None, profile=None):
    existing = portgroup_get(opts, host, name, profile=profile)
    spec = vim.host.PortGroup.Specification(
        name=name,
        vlanId=int(vlan_id) if vlan_id is not None else existing["vlan_id"],
        vswitchName=vswitch or existing["vswitch"],
        policy=vim.host.NetworkPolicy(),
    )
    _net(opts, host, profile=profile).UpdatePortGroup(pgName=name, portgrp=spec)


def portgroup_remove(opts, host, name, profile=None):
    _net(opts, host, profile=profile).RemovePortGroup(pgName=name)


def _pg_to_dict(pg):
    return {
        "name": pg.spec.name,
        "vlan_id": pg.spec.vlanId,
        "vswitch": pg.spec.vswitchName,
        "ports": len(pg.port or []),
    }


# ---------------------------------------------------------------------------
# VMkernel adapters
# ---------------------------------------------------------------------------


def vmkernel_list(opts, host, profile=None):
    info = _host(opts, host, profile=profile).config.network
    return [_vnic_to_dict(v) for v in (info.vnic or [])]


def vmkernel_get(opts, host, device, profile=None):
    for v in vmkernel_list(opts, host, profile=profile):
        if v["device"] == device:
            return v
    raise LookupError(f"vmkernel {device!r} not found on {host!r}")


def vmkernel_get_or_none(opts, host, device, profile=None):
    try:
        return vmkernel_get(opts, host, device, profile=profile)
    except LookupError:
        return None


def vmkernel_add(
    opts,
    host,
    portgroup,
    *,
    dhcp=False,
    ip_address=None,
    subnet_mask=None,
    mtu=1500,
    mac_address=None,
    nic_types=None,
    profile=None,
):
    """Add a VMkernel adapter on *portgroup*.

    Returns the new vmkernel device name (e.g. ``vmk1``).
    """
    if not dhcp and not (ip_address and subnet_mask):
        raise ValueError("provide dhcp=True OR (ip_address AND subnet_mask)")
    spec = vim.host.VirtualNic.Specification(
        ip=vim.host.IpConfig(
            dhcp=bool(dhcp),
            ipAddress=ip_address if not dhcp else None,
            subnetMask=subnet_mask if not dhcp else None,
        ),
        mtu=int(mtu),
    )
    if mac_address:
        spec.mac = mac_address
    if nic_types:
        spec.netStackInstanceKey = "defaultTcpipStack"
    device = _net(opts, host, profile=profile).AddVirtualNic(portgroup=portgroup, nic=spec)
    if nic_types:
        _select_traffic_types(opts, host, device, nic_types, profile=profile)
    return device


def vmkernel_update(
    opts,
    host,
    device,
    *,
    dhcp=None,
    ip_address=None,
    subnet_mask=None,
    mtu=None,
    profile=None,
):
    existing = vmkernel_get(opts, host, device, profile=profile)
    spec = vim.host.VirtualNic.Specification(
        ip=vim.host.IpConfig(
            dhcp=bool(dhcp) if dhcp is not None else existing["dhcp"],
            ipAddress=(ip_address if ip_address is not None else existing["ip_address"]),
            subnetMask=(subnet_mask if subnet_mask is not None else existing["subnet_mask"]),
        ),
        mtu=int(mtu) if mtu is not None else existing["mtu"],
    )
    _net(opts, host, profile=profile).UpdateVirtualNic(device=device, nic=spec)


def vmkernel_remove(opts, host, device, profile=None):
    _net(opts, host, profile=profile).RemoveVirtualNic(device=device)


def vmkernel_migrate(opts, host, device, dst_portgroup, profile=None):
    """Move VMkernel *device* from its current portgroup to *dst_portgroup*.

    Preserves IP/MTU/MAC by reading the current spec, removing, and re-adding
    on the destination portgroup. The device name (e.g. ``vmk2``) may change
    after the migration; the new name is returned.
    """
    existing = vmkernel_get(opts, host, device, profile=profile)
    vmkernel_remove(opts, host, device, profile=profile)
    return vmkernel_add(
        opts,
        host,
        dst_portgroup,
        dhcp=bool(existing.get("dhcp")),
        ip_address=existing.get("ip_address"),
        subnet_mask=existing.get("subnet_mask"),
        mtu=existing.get("mtu", 1500),
        mac_address=existing.get("mac_address"),
        profile=profile,
    )


def ipv6_get(opts, host, profile=None):
    """Return ``{enabled}`` for IPv6 on *host*'s network config."""
    h = _host(opts, host, profile=profile)
    return {"enabled": bool(getattr(h.config.network, "ipV6Enabled", False))}


def ipv6_set(opts, host, enabled, profile=None):
    """Enable or disable IPv6 on *host*. Reboot required to take effect."""
    cfg = vim.host.NetworkConfig()
    cfg.ipV6Enabled = bool(enabled)
    _net(opts, host, profile=profile).UpdateNetworkConfig(config=cfg, changeMode="modify")
    return ipv6_get(opts, host, profile=profile)


def vmkernel_set_traffic_types(opts, host, device, nic_types, profile=None):
    """Replace the traffic-type bitmap on a VMkernel adapter.

    *nic_types* is a list of strings — ``management``, ``vmotion``, ``vsan``,
    ``faultToleranceLogging``, ``vSphereReplication``, ``provisioning``,
    ``vSphereProvisioning``, ``vSphereBackupNFC``.
    """
    _select_traffic_types(opts, host, device, nic_types, profile=profile)


def _select_traffic_types(opts, host, device, nic_types, profile=None):
    h = _host(opts, host, profile=profile)
    vnic_mgr = h.configManager.virtualNicManager
    if vnic_mgr is None:
        raise LookupError("VMkernel manager not available on host")
    # First disable any current selection, then enable the desired set.
    for current in vnic_mgr.info.netConfig or []:
        for _sel in current.selectedVnic or []:
            try:
                vnic_mgr.DeselectVnicForNicType(nicType=current.nicType, device=device)
            except vim.fault.NotFound:
                continue
            except vim.fault.VimFault:
                continue
    for nic_type in nic_types:
        vnic_mgr.SelectVnicForNicType(nicType=nic_type, device=device)


def _vnic_to_dict(v):
    ip = v.spec.ip
    return {
        "device": v.device,
        "port": v.port,
        "portgroup": v.portgroup,
        "mac_address": v.spec.mac,
        "mtu": v.spec.mtu,
        "dhcp": bool(ip.dhcp) if ip else False,
        "ip_address": ip.ipAddress if ip else None,
        "subnet_mask": ip.subnetMask if ip else None,
    }


def physical_nic_list(opts, host, profile=None):
    """List physical NICs (``pnics``) on *host* — driver, link state, etc."""
    info = _host(opts, host, profile=profile).config.network
    out = []
    for p in info.pnic or []:
        ls = p.linkSpeed
        out.append(
            {
                "device": p.device,
                "driver": p.driver,
                "mac": p.mac,
                "duplex": ls.duplex if ls else None,
                "speed_mb": ls.speedMb if ls else None,
                "wake_on_lan_supported": bool(p.wakeOnLanSupported),
            }
        )
    return out
