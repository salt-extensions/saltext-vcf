"""vSAN disk and disk-group management (SOAP).

Two surfaces:

* Per-host via ``host.configManager.vsanSystem`` — claim disks, eject,
  query host status.
* Cluster-wide via ``VsanVcDiskManagementSystem`` at ``/vsanHealth`` —
  bulk disk-group operations across the cluster.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as vim_utils


def _find_host(opts, host_id_or_name, profile=None):
    content = vim_utils.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if not isinstance(dc, vim.Datacenter):
            continue
        for entity in dc.hostFolder.childEntity:
            hosts = []
            if isinstance(entity, vim.ClusterComputeResource):
                hosts = entity.host
            elif isinstance(entity, vim.ComputeResource):
                hosts = entity.host
            for host in hosts:
                if host_id_or_name in (host._moId, host.name):  # noqa: SLF001
                    return host
    raise LookupError(f"host {host_id_or_name!r} not found")


def host_status(opts, host_id_or_name, profile=None):
    """Return per-host vSAN status — node uuid, health, member count."""
    host = _find_host(opts, host_id_or_name, profile=profile)
    vs = host.configManager.vsanSystem
    info = vs.QueryHostStatus()
    return {
        "node_uuid": info.nodeUuid,
        "health": info.health,
        "uuid": info.uuid,
        "node_state": str(info.nodeState.state) if info.nodeState else None,
        "members_count": len(info.memberUuid) if info.memberUuid else 0,
    }


def host_config(opts, host_id_or_name, profile=None):
    """Return per-host vSAN config — enabled, storage info, cluster info."""
    host = _find_host(opts, host_id_or_name, profile=profile)
    vs = host.configManager.vsanSystem
    cfg = vs.config
    cluster_info = cfg.clusterInfo
    storage_info = cfg.storageInfo
    fd_info = getattr(cfg, "faultDomainInfo", None)
    return {
        "enabled": cfg.enabled,
        "cluster_uuid": cluster_info.uuid if cluster_info else None,
        "node_uuid": cluster_info.nodeUuid if cluster_info else None,
        "auto_claim_storage": storage_info.autoClaimStorage if storage_info else None,
        "disk_mapping_count": (
            len(cfg.storageInfo.diskMapping)
            if cfg.storageInfo and cfg.storageInfo.diskMapping
            else 0
        ),
        "fault_domain": fd_info.name if fd_info and fd_info.name else None,
        "vsan_esa_enabled": bool(getattr(cfg, "vsanEsaEnabled", False)),
    }


def host_disk_mapping(opts, host_id_or_name, profile=None):
    """Return per-host disk mappings (cache + capacity tier disks).

    Each entry: ``{"cache_disk", "capacity_disks", "non_ssd_disks"}``.
    """
    host = _find_host(opts, host_id_or_name, profile=profile)
    cfg = host.configManager.vsanSystem.config
    out = []
    for mapping in cfg.storageInfo.diskMapping or []:
        out.append(
            {
                "cache_disk": {
                    "canonical_name": mapping.ssd.canonicalName,
                    "uuid": (
                        mapping.ssd.vsanDiskInfo.vsanUuid if mapping.ssd.vsanDiskInfo else None
                    ),
                    "capacity_bytes": (
                        mapping.ssd.capacity.block * mapping.ssd.capacity.blockSize
                        if mapping.ssd.capacity
                        else None
                    ),
                },
                "capacity_disks": [
                    {
                        "canonical_name": d.canonicalName,
                        "uuid": d.vsanDiskInfo.vsanUuid if d.vsanDiskInfo else None,
                        "capacity_bytes": (
                            d.capacity.block * d.capacity.blockSize if d.capacity else None
                        ),
                    }
                    for d in (mapping.nonSsd or [])
                ],
            }
        )
    return out


def query_disks_for_filter(opts, host_id_or_name, profile=None):
    """List all disks (eligible and ineligible) for vSAN on a host.

    Returns the result of ``host.configManager.vsanSystem.QueryDisksForFilter()``
    in dict form: ``state`` (eligible/ineligible/in_use), ``error`` (when
    ineligible), ``vsan_disk`` (uuid + state).
    """
    host = _find_host(opts, host_id_or_name, profile=profile)
    vs = host.configManager.vsanSystem
    return [
        {
            "canonical_name": e.disk.canonicalName,
            "state": str(e.state),
            "error": str(e.error) if e.error else None,
            "vsan_uuid": e.disk.vsanDiskInfo.vsanUuid if e.disk.vsanDiskInfo else None,
        }
        for e in (vs.QueryDisksForVsan() or [])
    ]


def add_disks(opts, host_id_or_name, disks, profile=None):
    """Claim disks for vSAN on *host_id_or_name*.

    *disks* is a list of canonical names (e.g. ``["naa.6...", ...]``).
    Returns the vim.Task moId.
    """
    host = _find_host(opts, host_id_or_name, profile=profile)
    vs = host.configManager.vsanSystem
    # vSAN expects ScsiDisk objects from the host's storage system.
    storage = host.configManager.storageSystem
    by_canonical = {d.canonicalName: d for d in (storage.storageDeviceInfo.scsiLun or [])}
    selected = [by_canonical[c] for c in disks if c in by_canonical]
    if not selected:
        raise LookupError(f"none of {disks!r} found on host {host.name}")
    task = vs.AddDisks_Task(disk=selected)
    return task._moId  # noqa: SLF001


def remove_disks(
    opts,
    host_id_or_name,
    disks,
    maintenance_mode_action="ensureObjectAccessibility",
    profile=None,
):
    """Eject disks from vSAN on *host_id_or_name* (uses MaintenanceSpec).

    *maintenance_mode_action* is one of:
        ensureObjectAccessibility | noAction | evacuateAllData
    """
    host = _find_host(opts, host_id_or_name, profile=profile)
    vs = host.configManager.vsanSystem
    storage = host.configManager.storageSystem
    by_canonical = {d.canonicalName: d for d in (storage.storageDeviceInfo.scsiLun or [])}
    selected = [by_canonical[c] for c in disks if c in by_canonical]
    if not selected:
        raise LookupError(f"none of {disks!r} found on host {host.name}")
    spec = vim.host.MaintenanceSpec()
    spec.vsanMode = vim.vsan.host.DecommissionMode()
    spec.vsanMode.objectAction = maintenance_mode_action
    task = vs.RemoveDisk_Task(disk=selected, maintenanceSpec=spec)
    return task._moId  # noqa: SLF001
