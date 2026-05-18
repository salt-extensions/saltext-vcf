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
    profile=None,
):
    """Create a VDS in *datacenter*'s networkFolder.

    *version* defaults to vCenter's latest supported (omit for auto).
    """
    dc = _datacenter(opts, datacenter, profile=profile)
    folder = dc.networkFolder
    uplink_names = [f"uplink{i + 1}" for i in range(int(num_uplinks))]
    cfg = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(
        name=name,
        maxMtu=int(max_mtu),
        description=description,
        uplinkPortPolicy=vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy(
            uplinkPortName=uplink_names
        ),
    )
    spec = vim.DistributedVirtualSwitch.CreateSpec(configSpec=cfg)
    if version:
        spec.productInfo = vim.dvs.ProductSpec(version=version)
    task = folder.CreateDVS_Task(spec=spec)
    return task._moId  # noqa: SLF001


def reconfigure(opts, name_or_id, *, max_mtu=None, description=None, profile=None):
    """Update VDS config fields. Only non-None fields are applied."""
    dvs = _dvs(opts, name_or_id, profile=profile)
    cfg = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
    cfg.configVersion = dvs.config.configVersion
    if max_mtu is not None:
        cfg.maxMtu = int(max_mtu)
    if description is not None:
        cfg.description = description
    task = dvs.ReconfigureDvs_Task(spec=cfg)
    return task._moId  # noqa: SLF001


def delete(opts, name_or_id, profile=None):
    dvs = _dvs(opts, name_or_id, profile=profile)
    task = dvs.Destroy_Task()
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
    return task._moId  # noqa: SLF001
