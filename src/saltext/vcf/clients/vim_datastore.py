"""vCenter-level datastore lifecycle via SOAP (``vim.Datastore``).

Port of ``vmware_datastore`` from ``saltext.vmware``:

* ``get`` / ``list_`` — summary + VMFS volume info (uuid, extents,
  maintenanceMode, multipleHostAccess, uncommitted, folder path).
* ``enter_maintenance`` / ``exit_maintenance`` — datastore SDRS
  maintenance (``DatastoreEnterMaintenanceMode`` /
  ``DatastoreExitMaintenanceMode_Task``).
* ``disk_partitions`` — per-disk partition table via
  ``HostStorageSystem.RetrieveDiskPartitionInfo``.

Per-host VMFS create/mount lives in :mod:`saltext.vcf.clients.vim_host_datastore`.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _find_datastore(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    try:
        for ds in container.view:
            if name_or_id in (ds._moId, ds.name):  # noqa: SLF001
                return ds
    finally:
        container.Destroy()
    raise LookupError(f"datastore {name_or_id!r} not found")


def _inventory_path(node, root):
    parts = []
    depth = 0
    while node is not None and depth < 64:
        depth += 1
        try:
            if node._moId == root._moId:  # noqa: SLF001
                break
        except AttributeError:
            break
        try:
            name = node.name
            if not isinstance(name, str):
                break
            parts.append(name)
        except AttributeError:
            break
        node = getattr(node, "parent", None)
    return "/" + "/".join(reversed(parts))


def _to_dict(ds, root):
    summary = ds.summary
    info = getattr(ds, "info", None)
    vmfs = getattr(info, "vmfs", None)
    out = {
        "moid": ds._moId,  # noqa: SLF001
        "name": summary.name,
        "type": summary.type,
        "accessible": bool(summary.accessible),
        "capacity": int(summary.capacity) if summary.capacity is not None else None,
        "free_space": int(summary.freeSpace) if summary.freeSpace is not None else None,
        "maintenance_mode": str(summary.maintenanceMode),
        "multiple_host_access": bool(summary.multipleHostAccess),
        "uncommitted": int(summary.uncommitted) if summary.uncommitted else 0,
        "url": summary.url,
        "folder": _inventory_path(ds, root),
    }
    if vmfs is not None:
        out["vmfs"] = {
            "uuid": vmfs.uuid,
            "name": vmfs.name,
            "local": bool(vmfs.local),
            "extents": [e.diskName for e in (vmfs.extent or [])],
            "block_size_mb": getattr(vmfs, "blockSizeMb", None),
        }
    return out


def get(opts, datastore, profile=None):
    """Return the full datastore dict for *datastore* (MoID or name)."""
    ds = _find_datastore(opts, datastore, profile=profile)
    return _to_dict(ds, soap.content(opts, profile=profile).rootFolder)


def get_or_none(opts, datastore, profile=None):
    try:
        return get(opts, datastore, profile=profile)
    except LookupError:
        return None


def list_(
    opts,
    *,
    datacenter=None,
    cluster=None,
    host=None,
    datastore_names=None,
    backing_disk_ids=None,
    backing_disk_scsi_addresses=None,
    profile=None,
):
    """List datastores with VMFS detail and optional filters.

    Filters mirror ``vmware_datastore.list_datastores``: by names, by
    backing-disk canonical names, or by backing-disk scsi addresses
    (converted via the host's storage system).
    """
    content = soap.content(opts, profile=profile)
    root = content.rootFolder
    names = set(datastore_names) if datastore_names else None
    out = []
    container = content.viewManager.CreateContainerView(root, [vim.Datastore], True)
    try:
        for ds in container.view:
            d = _to_dict(ds, root)
            if names and d["name"] not in names:
                continue
            if datacenter is not None:
                dc_name = _walk_dc_name(ds)
                if dc_name != datacenter and not _is_in_datacenter(ds, datacenter, content):
                    continue
            if cluster is not None and not _is_in_cluster(ds, cluster, content):
                continue
            if host is not None and not _is_on_host(ds, host, content):
                continue
            if backing_disk_ids is not None:
                extents = set((d.get("vmfs") or {}).get("extents") or [])
                if not extents.intersection(set(backing_disk_ids)):
                    continue
            if backing_disk_scsi_addresses is not None:
                # Scsi-address form: match against devicePath of LUNs on hosts
                # that mount the datastore (best-effort).
                matched = False
                for mnt in (getattr(ds, "host", None) or []):
                    h = getattr(mnt, "key", None)
                    storage = getattr(h, "configManager", None)
                    storage = getattr(storage, "storageSystem", None) if storage else None
                    if storage is None:
                        continue
                    for lun in (storage.storageDeviceInfo.scsiLun or []):
                        if lun.devicePath in set(backing_disk_scsi_addresses):
                            if lun.canonicalName in set(
                                (d.get("vmfs") or {}).get("extents") or []
                            ):
                                matched = True
                if not matched:
                    continue
            out.append(d)
    finally:
        container.Destroy()
    return out


def _walk_dc_name(obj):
    node = obj
    while node is not None:
        if isinstance(node, vim.Datacenter):
            return node.name
        node = getattr(node, "parent", None)
    return None


def _is_in_datacenter(ds, datacenter, content):
    node = ds
    while node is not None:
        if isinstance(node, vim.Datacenter) and datacenter in (node._moId, node.name):  # noqa: SLF001
            return True
        node = getattr(node, "parent", None)
    return False


def _is_in_cluster(ds, cluster, content):
    for mnt in (getattr(ds, "host", None) or []):
        h = mnt.key
        node = h
        while node is not None:
            if getattr(node, "name", None) == cluster or getattr(node, "_moId", None) == cluster:  # noqa: SLF001
                return True
            node = getattr(node, "parent", None)
    return False


def _is_on_host(ds, host, content):
    for mnt in (getattr(ds, "host", None) or []):
        h = mnt.key
        if host in (getattr(h, "_moId", None), getattr(h, "name", None)):  # noqa: SLF001
            return True
    return False


# ---------------------------------------------------------------------------
# Datastore maintenance mode
# ---------------------------------------------------------------------------


def enter_maintenance(opts, datastore, profile=None):
    """Put the datastore in maintenance mode (synchronous call)."""
    ds = _find_datastore(opts, datastore, profile=profile)
    result = ds.DatastoreEnterMaintenanceMode()
    return {"maintenanceMode": "inMaintenance" if result else "failed to enter maintenance mode"}


def exit_maintenance(opts, datastore, profile=None):
    """Take the datastore out of maintenance mode. Returns the task moId."""
    ds = _find_datastore(opts, datastore, profile=profile)
    task = ds.DatastoreExitMaintenanceMode_Task()
    soap.wait_for_task(task)
    return {"maintenanceMode": "normal"}


# ---------------------------------------------------------------------------
# Disk partitions
# ---------------------------------------------------------------------------


def disk_partitions(opts, host, *, disk_id=None, scsi_address=None, profile=None):
    """List the partition table of a disk on *host*.

    Either *disk_id* (canonical name) or *scsi_address* must be given;
    the canonical name wins. Uses
    ``HostStorageSystem.RetrieveDiskPartitionInfo(devicePath)``.
    """
    from saltext.vcf.clients import vim_host_storage as host_storage  # noqa: PLC0415

    if not disk_id and not scsi_address:
        raise ValueError("provide disk_id or scsi_address")
    storage = host_storage._ss(host_storage._host(opts, host, profile=profile))  # noqa: SLF001
    if not disk_id:
        for lun in (storage.storageDeviceInfo.scsiLun or []):
            if lun.devicePath == scsi_address:
                disk_id = lun.canonicalName
                break
        if not disk_id:
            raise LookupError(f"scsi lun with address {scsi_address!r} not found on {host!r}")
    device_path = None
    for lun in (storage.storageDeviceInfo.scsiLun or []):
        if lun.canonicalName == disk_id:
            device_path = lun.devicePath
            break
    if device_path is None:
        raise LookupError(f"disk {disk_id!r} not found on {host!r}")
    info = storage.RetrieveDiskPartitionInfo(devicePath=device_path)[0]
    out = []
    for spec in info.spec.partition:
        layout = next(
            (p for p in info.layout.partition if p.partition == spec.partition), None
        )
        sectors = spec.endSector - spec.startSector + 1
        size_kb = None
        if layout is not None:
            size_kb = (
                (layout.end.block - layout.start.block + 1) * layout.start.blockSize / 1024
            )
        out.append(
            {
                "device": disk_id,
                "format": info.spec.partitionFormat,
                "partition": spec.partition,
                "type": spec.type,
                "sectors": sectors,
                "size_kb": size_kb,
            }
        )
    return out
