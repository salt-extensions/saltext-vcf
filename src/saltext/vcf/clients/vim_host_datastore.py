"""Host datastore lifecycle via SOAP.

Mounts and unmounts VMFS / NFS / NAS datastores on a single ESXi host.
The REST ``/api/vcenter/datastore`` surface is read-only; for create/mount
we go through ``HostDatastoreSystem``.

Surfaces:

- **VMFS** — create on a raw disk path: ``HostDatastoreSystem.CreateVmfsDatastore``.
- **NFS / NAS** — mount a remote share: ``HostDatastoreSystem.CreateNasDatastore``.
- **Detach / Unmount** — ``RemoveDatastore``.
- **Rescan** — ``RescanAllHba``.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _resolve_host(opts, name_or_id, profile=None):
    """Thin wrapper around :func:`saltext.vcf.utils.vim.resolve_host_system`."""
    return soap.resolve_host_system(opts, name_or_id, profile=profile)


def list_(opts, host, profile=None):
    """List all datastores mounted on *host*."""
    h = _resolve_host(opts, host, profile=profile)
    out = []
    for ds in h.datastore or []:
        summary = ds.summary
        out.append(
            {
                "moid": ds._moId,  # noqa: SLF001
                "name": summary.name,
                "type": summary.type,
                "url": summary.url,
                "capacity_bytes": int(summary.capacity),
                "free_bytes": int(summary.freeSpace),
                "accessible": bool(summary.accessible),
            }
        )
    return out


def list_available_vmfs_disks(opts, host, profile=None):
    """Return raw disk devices on *host* eligible for a new VMFS datastore."""
    h = _resolve_host(opts, host, profile=profile)
    out = []
    for disk in h.configManager.datastoreSystem.QueryAvailableDisksForVmfs() or []:
        out.append(
            {
                "device_path": disk.devicePath,
                "canonical_name": disk.canonicalName,
                "size_bytes": int(disk.capacity.block) * int(disk.capacity.blockSize),
                "ssd": bool(getattr(disk, "ssd", False)),
            }
        )
    return out


# ---------------------------------------------------------------------------
# VMFS
# ---------------------------------------------------------------------------


def create_vmfs(opts, host, name, device_path, vmfs_version=6, profile=None):
    """Create a VMFS datastore on *device_path* on *host*. Synchronous (no task).

    *vmfs_version*: 5 or 6 (vSphere 7+ defaults to 6).
    """
    h = _resolve_host(opts, host, profile=profile)
    ds_system = h.configManager.datastoreSystem
    options = ds_system.QueryVmfsDatastoreCreateOptions(devicePath=device_path)
    if not options:
        raise RuntimeError(f"no VMFS create options reported for {device_path!r}")
    spec = options[0].spec
    spec.vmfs.volumeName = name
    spec.vmfs.majorVersion = int(vmfs_version)
    ds = ds_system.CreateVmfsDatastore(spec=spec)
    return ds._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# NFS / NAS
# ---------------------------------------------------------------------------


def mount_nfs(
    opts,
    host,
    name,
    remote_host,
    remote_path,
    access_mode="readWrite",
    type_="NFS",
    profile=None,
):
    """Mount an NFS share on *host* and return the new datastore moid.

    *type_*: ``NFS`` (v3, default) or ``NFS41``.
    *access_mode*: ``readOnly`` or ``readWrite``.
    """
    h = _resolve_host(opts, host, profile=profile)
    ds_system = h.configManager.datastoreSystem
    spec = vim.host.NasVolume.Specification(
        remoteHost=remote_host,
        remotePath=remote_path,
        localPath=name,
        accessMode=access_mode,
        type=type_,
    )
    ds = ds_system.CreateNasDatastore(spec=spec)
    return ds._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Removal / rescan
# ---------------------------------------------------------------------------


def remove(opts, host, datastore, profile=None):
    """Unmount / remove a datastore from *host*. Synchronous."""
    h = _resolve_host(opts, host, profile=profile)
    ds_system = h.configManager.datastoreSystem
    for ds in h.datastore or []:
        if datastore in (ds._moId, ds.name):  # noqa: SLF001
            ds_system.RemoveDatastore(datastore=ds)
            return True
    raise LookupError(f"datastore {datastore!r} not found on host {host!r}")


def rescan_storage(opts, host, profile=None):
    """Trigger ``RescanAllHba`` on *host*. Synchronous."""
    h = _resolve_host(opts, host, profile=profile)
    h.configManager.storageSystem.RescanAllHba()
    return True


# ---------------------------------------------------------------------------
# VMFS extent / backing-disk inventory + mount/unmount by uuid
# (vmware_esxi.get_lun_ids / get_host_disks / vmware_datastore.mount_datastore parity)
# ---------------------------------------------------------------------------


def _find_host(opts, name_or_id, profile=None):
    return _resolve_host(opts, name_or_id, profile=profile)


def lun_ids(opts, host, profile=None):
    """Return the LUN canonical names backing every datastore visible to *host*."""
    h = _find_host(opts, host, profile=profile)
    ids = set()
    for ds in h.datastore or []:
        info = getattr(ds, "info", None)
        vmfs = getattr(info, "vmfs", None)
        if vmfs is None:
            continue
        for extent in vmfs.extent or []:
            ids.add(extent.diskName)
    return sorted(ids)


def disks(opts, host, disk_name=None, profile=None):
    """Return per-datastore VMFS backing-disk info on *host*.

    Shape per entry: ``{scsi_address, name, uuid, local}`` where *name*
    is the VMFS volume name (filterable via *disk_name*).
    """
    h = _find_host(opts, host, profile=profile)
    out = []
    for ds in h.datastore or []:
        info = getattr(ds, "info", None)
        vmfs = getattr(info, "vmfs", None)
        if vmfs is None:
            continue
        if disk_name and vmfs.name != disk_name:
            continue
        for extent in vmfs.extent or []:
            out.append(
                {
                    "scsi_address": extent.diskName,
                    "name": vmfs.name,
                    "uuid": vmfs.uuid,
                    "local": bool(vmfs.local),
                }
            )
    return out


def mount_vmfs(opts, host, vmfs_uuid, lun_canonical_name=None, *, datastore_name=None, profile=None):
    """Attach a LUN and mount an *existing* VMFS volume by uuid on *host*.

    Handles the unresolved-volume case (same-uuid clone conflicts) with
    ``QueryUnresolvedVmfsVolume`` + ``ResolveMultipleUnresolvedVmfsVolumes``
    using ``uuidResolution="forceMounted"``. Returns a step log.
    """
    h = _find_host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    steps = []
    if lun_canonical_name:
        try:
            storage.AttachScsiLun(lunCanonicalName=lun_canonical_name)
            steps.append(f"attached disk {lun_canonical_name} to {h.name}")
        except vim.fault.InvalidState:
            steps.append(f"disk {lun_canonical_name} already attached to {h.name}")
        storage.RefreshStorageSystem()
    try:
        storage.MountVmfsVolume(vmfs_uuid)
        steps.append(f"mounted vmfs {vmfs_uuid} on {h.name}")
    except vim.fault.NotFound:
        steps.append(f"vmfs {vmfs_uuid} not found — resolving conflicts")
        unresolved = storage.QueryUnresolvedVmfsVolume() or []
        for vol in unresolved:
            if vol.vmfsUuid != vmfs_uuid:
                continue
            if vol.resolveStatus.resolvable:
                steps.append(f"{vmfs_uuid} has a resolvable conflict")
                spec = vim.host.UnresolvedVmfsResolutionSpec()
                spec.extentDevicePath = [e.devicePath for e in vol.extent]
                spec.uuidResolution = "forceMounted"
                storage.ResolveMultipleUnresolvedVmfsVolumes([spec])
                steps.append(f"resolved {vmfs_uuid}")
            else:
                raise RuntimeError(f"{vmfs_uuid} has an unresolvable conflict on {h.name}")
    except vim.fault.InvalidState:
        steps.append(f"vmfs {vmfs_uuid} already mounted on {h.name}")
    storage.RefreshStorageSystem()
    return steps


def unmount_vmfs(opts, host, vmfs_uuid, *, detach_luns=True, profile=None):
    """Unmount the VMFS volume *vmfs_uuid* on *host* and optionally detach its LUNs.

    The datastore stays registered for other hosts. Returns a step log.
    """
    h = _find_host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    steps = []
    mount_infos = getattr(storage.fileSystemVolumeInfo, "mountInfo", None) or []
    volume = None
    for mi in mount_infos:
        vol = mi.volume
        if getattr(vol, "uuid", None) == vmfs_uuid:
            volume = vol
            break
    if volume is None:
        raise LookupError(f"vmfs volume {vmfs_uuid!r} not found on {h.name}")
    try:
        storage.UnmountVmfsVolume(vmfs_uuid)
        steps.append(f"unmounted vmfs {vmfs_uuid} from {h.name}")
    except Exception as exc:  # pylint: disable=broad-except
        if "not mounted" in str(exc).lower() or getattr(exc, "name", "") == "InvalidState":
            steps.append(f"vmfs {vmfs_uuid} not mounted on {h.name}")
        else:
            raise
    if detach_luns:
        for extent in volume.extent or []:
            try:
                storage.DetachScsiLun(lunCanonicalName=extent.diskName)
                steps.append(f"detached disk {extent.diskName} from {h.name}")
            except Exception as exc:  # pylint: disable=broad-except
                steps.append(f"detach {extent.diskName} skipped: {exc}")
    storage.RefreshStorageSystem()
    return steps
