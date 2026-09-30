"""vSphere Distributed Virtual Switch (VDS) lifecycle via SOAP.

VDS objects can't be created through vCenter REST in VCF 9.x; the
canonical path is ``Folder.CreateDVS_Task`` with a
``vim.DistributedVirtualSwitch.CreateSpec``. Reconfigure uses
``DistributedVirtualSwitch.ReconfigureDvs_Task``.

A VDS is conceptually a switch + a set of uplink ports + a member list of
ESXi hosts. Each host attaches with a ``HostMemberConfigSpec`` mapping its
physical NICs to the switch's uplinks.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap

# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def _dvs(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.DistributedVirtualSwitch], True
    )
    try:
        for dvs in container.view:
            if name_or_id in (dvs._moId, dvs.name, dvs.uuid):  # noqa: SLF001
                return dvs
    finally:
        container.Destroy()
    raise LookupError(f"DVS {name_or_id!r} not found")


def _datacenter(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if isinstance(dc, vim.Datacenter) and name_or_id in (
            dc._moId,  # noqa: SLF001
            dc.name,
        ):
            return dc
    raise LookupError(f"datacenter {name_or_id!r} not found")


def _host(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for h in container.view:
            if name_or_id in (h._moId, h.name):  # noqa: SLF001
                return h
    finally:
        container.Destroy()
    raise LookupError(f"host {name_or_id!r} not found")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def list_(opts, profile=None):
    """Return a list of ``{moid, name, uuid, version, num_ports, max_mtu, hosts}`` dicts."""
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.DistributedVirtualSwitch], True
    )
    try:
        return [_to_dict(dvs) for dvs in container.view]
    finally:
        container.Destroy()


def get(opts, name_or_id, profile=None):
    return _to_dict(_dvs(opts, name_or_id, profile=profile))


def get_or_none(opts, name_or_id, profile=None):
    try:
        return get(opts, name_or_id, profile=profile)
    except LookupError:
        return None


def _to_dict(dvs):
    cfg = dvs.config
    return {
        "moid": dvs._moId,  # noqa: SLF001
        "name": dvs.name,
        "uuid": dvs.uuid,
        "version": cfg.productInfo.version if cfg.productInfo else None,
        "num_ports": cfg.numPorts,
        "max_mtu": cfg.maxMtu,
        "hosts": [
            m.config.host._moId for m in (cfg.host or []) if m.config and m.config.host
        ],  # noqa: SLF001
        "uplink_port_names": list(
            (cfg.uplinkPortPolicy.uplinkPortName if cfg.uplinkPortPolicy else []) or []
        ),
    }


# ---------------------------------------------------------------------------
# Create / Reconfigure / Delete
# ---------------------------------------------------------------------------


def create(
    opts,
    name,
    datacenter,
    *,
    version=None,
    num_uplinks=4,
    max_mtu=1500,
    description="",
    uplink_prefix="uplink",
    discovery_protocol=None,
    discovery_operation=None,
    multicast_filtering_mode=None,
    contact_name=None,
    contact_description=None,
    network_promiscuous=None,
    network_mac_changes=None,
    network_forged_transmits=None,
    health_check_vlan_mtu=None,
    health_check_vlan_mtu_interval=None,
    health_check_teaming_failover=None,
    health_check_teaming_failover_interval=None,
    profile=None,
):
    """Create a VDS in *datacenter*'s networkFolder (full spec surface).

    *version* defaults to vCenter's latest supported (omit for auto).
    *uplink_prefix* names the uplinks (``uplink1``..``uplinkN``).
    *discovery_protocol*: ``cdp`` | ``lldp`` | ``disabled``;
    *discovery_operation*: ``both`` | ``advertise`` | ``listen``.
    *multicast_filtering_mode*: ``basic`` | ``snooping``.
    The security policy and health-check knobs are applied post-create
    via :func:`reconfigure` when the switch exists; on creation they are
    embedded in the initial config spec.
    """
    dc = _datacenter(opts, datacenter, profile=profile)
    folder = dc.networkFolder
    uplink_names = [f"{uplink_prefix}{i + 1}" for i in range(int(num_uplinks))]
    cfg = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
        name=name,
        maxMtu=int(max_mtu),
        description=description,
        uplinkPortPolicy=vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy(
            uplinkPortName=uplink_names
        ),
    )
    _apply_optional_cfg(cfg, discovery_protocol, discovery_operation, multicast_filtering_mode,
                        contact_name, contact_description)
    _apply_security_policy(cfg, network_promiscuous, network_mac_changes, network_forged_transmits)
    spec = vim.DistributedVirtualSwitch.CreateSpec(configSpec=cfg)
    if version:
        spec.productInfo = vim.dvs.ProductSpec(version=version)
    task = folder.CreateDVS_Task(spec=spec)
    soap.wait_for_task(task)
    if any(
        v is not None
        for v in (
            health_check_vlan_mtu,
            health_check_vlan_mtu_interval,
            health_check_teaming_failover,
            health_check_teaming_failover_interval,
        )
    ):
        reconfigure(
            opts,
            task._moId,  # noqa: SLF001
            max_mtu=max_mtu,
            health_check_vlan_mtu=health_check_vlan_mtu,
            health_check_vlan_mtu_interval=health_check_vlan_mtu_interval,
            health_check_teaming_failover=health_check_teaming_failover,
            health_check_teaming_failover_interval=health_check_teaming_failover_interval,
            profile=profile,
        )
    return task._moId  # noqa: SLF001


def _apply_optional_cfg(cfg, discovery_protocol, discovery_operation, multicast_filtering_mode,
                        contact_name, contact_description):
    if discovery_protocol or discovery_operation:
        ldp = vim.host.LinkDiscoveryProtocolConfig()
        if discovery_protocol == "disabled":
            ldp.protocol = "cdp"
            ldp.operation = "none"
        else:
            ldp.protocol = discovery_protocol
            ldp.operation = discovery_operation
        cfg.linkDiscoveryProtocolConfig = ldp
    if multicast_filtering_mode:
        cfg.multicastFilteringMode = (
            "legacyFiltering" if multicast_filtering_mode == "basic" else multicast_filtering_mode
        )
    if contact_name or contact_description:
        cfg.contact = vim.DistributedVirtualSwitch.ContactInfo(
            contact=contact_description, name=contact_name
        )


def _apply_security_policy(
    cfg, network_promiscuous, network_mac_changes, network_forged_transmits, current_policy=None
):
    """Build the DVS-level security policy onto ``cfg.defaultPortConfig``.

    The default port config for a VmwareDVSwitch is a
    ``VmwarePortConfigPolicy`` (the ConfigSpec's declared ``Setting``
    type has no ``securityPolicy`` field); pyVmomi serializes the
    assigned class. Unset fields inherit from *current_policy*.
    """
    if network_promiscuous is None and network_mac_changes is None and network_forged_transmits is None:
        return
    policy = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
    for field, want in (
        ("allowPromiscuous", network_promiscuous),
        ("macChanges", network_mac_changes),
        ("forgedTransmits", network_forged_transmits),
    ):
        if want is not None:
            setattr(policy, field, vim.BoolPolicy(value=bool(want)))
        elif current_policy is not None and getattr(current_policy, field, None) is not None:
            setattr(policy, field, getattr(current_policy, field))
    dpc = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
    dpc.securityPolicy = policy
    cfg.defaultPortConfig = dpc


def reconfigure(
    opts,
    name_or_id,
    *,
    max_mtu=None,
    description=None,
    uplink_prefix=None,
    num_uplinks=None,
    discovery_protocol=None,
    discovery_operation=None,
    multicast_filtering_mode=None,
    contact_name=None,
    contact_description=None,
    network_promiscuous=None,
    network_mac_changes=None,
    network_forged_transmits=None,
    health_check_vlan_mtu=None,
    health_check_vlan_mtu_interval=None,
    health_check_teaming_failover=None,
    health_check_teaming_failover_interval=None,
    version=None,
    profile=None,
):
    """Update VDS config fields (full spec surface). Only non-None fields are applied.

    *uplink_prefix* + *num_uplinks* rebuild the uplink-port name array.
    *version* updates the switch product version via a second
    ``ReconfigureDvs_Task`` with a ``ProductSpec``.
    """
    dvs = _dvs(opts, name_or_id, profile=profile)
    cfg = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
    cfg.configVersion = dvs.config.configVersion
    if max_mtu is not None:
        cfg.maxMtu = int(max_mtu)
    if description is not None:
        cfg.description = description
    if num_uplinks is not None:
        prefix = uplink_prefix or "uplink"
        cfg.uplinkPortPolicy = vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy(
            uplinkPortName=[f"{prefix}{i + 1}" for i in range(int(num_uplinks))]
        )
    _apply_optional_cfg(cfg, discovery_protocol, discovery_operation, multicast_filtering_mode,
                        contact_name, contact_description)
    if discovery_protocol or discovery_operation or multicast_filtering_mode or contact_name or contact_description:
        # preserve current values for fields not provided
        current = dvs.config
        if cfg.linkDiscoveryProtocolConfig is None and getattr(current, "linkDiscoveryProtocolConfig", None):
            cfg.linkDiscoveryProtocolConfig = current.linkDiscoveryProtocolConfig
        if cfg.multicastFilteringMode is None and getattr(current, "multicastFilteringMode", None):
            cfg.multicastFilteringMode = current.multicastFilteringMode
        if cfg.contact is None and getattr(current, "contact", None):
            cfg.contact = current.contact
    current_policy = getattr(getattr(dvs.config, "defaultPortConfig", None), "securityPolicy", None)
    _apply_security_policy(
        cfg, network_promiscuous, network_mac_changes, network_forged_transmits,
        current_policy=current_policy,
    )
    task = dvs.ReconfigureDvs_Task(spec=cfg)
    soap.wait_for_task(task)
    if version is not None:
        vcfg = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        vcfg.configVersion = dvs.config.configVersion
        task = dvs.ReconfigureDvs_Task(spec=vcfg, productSpec=vim.dvs.ProductSpec(version=version))
        soap.wait_for_task(task)
    if any(
        v is not None
        for v in (
            health_check_vlan_mtu,
            health_check_vlan_mtu_interval,
            health_check_teaming_failover,
            health_check_teaming_failover_interval,
        )
    ):
        _update_health_checks(
            dvs,
            vlan_mtu=health_check_vlan_mtu,
            vlan_mtu_interval=health_check_vlan_mtu_interval,
            teaming_failover=health_check_teaming_failover,
            teaming_failover_interval=health_check_teaming_failover_interval,
        )
    return task._moId  # noqa: SLF001


def _update_health_checks(dvs, *, vlan_mtu=None, vlan_mtu_interval=None,
                           teaming_failover=None, teaming_failover_interval=None):
    configs = list(getattr(dvs.config, "healthCheckConfig", None) or [])
    if not configs:
        return None
    health = []
    for cfg in configs:
        if isinstance(cfg, vim.dvs.VmwareDistributedVirtualSwitch.VlanMtuHealthCheckConfig):
            if vlan_mtu is not None:
                cfg.enable = bool(vlan_mtu)
            if vlan_mtu_interval is not None:
                cfg.interval = int(vlan_mtu_interval)
            health.append(cfg)
        elif isinstance(cfg, vim.dvs.VmwareDistributedVirtualSwitch.TeamingHealthCheckConfig):
            if teaming_failover is not None:
                cfg.enable = bool(teaming_failover)
            if teaming_failover_interval is not None:
                cfg.interval = int(teaming_failover_interval)
            health.append(cfg)
    if health:
        dvs.UpdateHealthCheckConfig(healthCheckConfig=health)
    return health


def delete(opts, name_or_id, profile=None):
    dvs = _dvs(opts, name_or_id, profile=profile)
    task = dvs.Destroy_Task()
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Host membership
# ---------------------------------------------------------------------------


def add_host(opts, dvs_name_or_id, host_name_or_id, *, pnic_devices=None, profile=None):
    """Attach *host* to the DVS, optionally pinning *pnic_devices* (e.g. ``["vmnic0"]``) to uplinks."""
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    host = _host(opts, host_name_or_id, profile=profile)
    backing = vim.dvs.HostMember.PnicBacking()
    for pnic in pnic_devices or []:
        backing.pnicSpec.append(vim.dvs.HostMember.PnicSpec(pnicDevice=pnic))
    member_cfg = vim.dvs.HostMember.ConfigSpec(
        operation="add",
        host=host,
        backing=backing,
    )
    spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
        configVersion=dvs.config.configVersion,
        host=[member_cfg],
    )
    task = dvs.ReconfigureDvs_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001


def remove_host(opts, dvs_name_or_id, host_name_or_id, profile=None):
    dvs = _dvs(opts, dvs_name_or_id, profile=profile)
    host = _host(opts, host_name_or_id, profile=profile)
    member_cfg = vim.dvs.HostMember.ConfigSpec(operation="remove", host=host)
    spec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
        configVersion=dvs.config.configVersion,
        host=[member_cfg],
    )
    task = dvs.ReconfigureDvs_Task(spec=spec)
    soap.wait_for_task(task)
    return task._moId  # noqa: SLF001
