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
