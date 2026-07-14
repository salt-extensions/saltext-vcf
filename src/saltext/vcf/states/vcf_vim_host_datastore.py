"""
State module for host datastore lifecycle (VMFS / NFS).

Idempotent wrappers over :mod:`saltext.vcf.modules.vcf_vim_host_datastore`.
Works against both vCenter-managed hosts (``saltext.vcf.vcenter`` pillar)
and standalone ESXi hosts (``saltext.vcf.esxi`` pillar) — the underlying
client picks the right connection path automatically.

Example — declare a VMFS datastore on a standalone ESXi host::

    ssd-4tb-vmfs:
      vcf_vim_host_datastore.vmfs_present:
        - name: datastore-ssd-4tb
        - host: 192.168.0.24
        - device_path: /vmfs/devices/disks/t10.ATA_____T2DFORCE_...

Or mount an NFS export::

    nas-scratch:
      vcf_vim_host_datastore.nfs_mounted:
        - name: scratch
        - host: 192.168.0.24
        - remote_host: nfs.example.test
        - remote_path: /export/scratch
"""

__virtualname__ = "vcf_vim_host_datastore"


def __virtual__():
    return __virtualname__


def _find(host, name, profile):
    """Return the datastore dict named *name* on *host*, or None."""
    for ds in __salt__["vcf_vim_host_datastore.list_"](host, profile=profile) or []:
        if ds.get("name") == name:
            return ds
    return None


def vmfs_present(name, host, device_path, vmfs_version=6, profile=None):
    """
    Ensure a VMFS datastore called *name* exists on *host*, created on
    *device_path* if missing.

    :param name: Datastore label (also the ``name`` argument to the state).
    :param host: ESXi host FQDN, IP, MOID, or arbitrary caller label when
        talking to a standalone host (which has only one HostSystem).
    :param device_path: Full ``/vmfs/devices/disks/…`` path of the raw disk.
    :param vmfs_version: 5 or 6.  vSphere 7+ defaults to 6.
    :param profile: Optional pillar profile override.
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    existing = _find(host, name, profile)
    if existing:
        gib = existing.get("capacity_bytes", 0) // (1024**3)
        ret["comment"] = f"VMFS datastore {name!r} already present on {host} ({gib} GiB)."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = (
            f"Would create VMFS{vmfs_version} datastore {name!r} on {host} "
            f"from device {device_path}."
        )
        ret["changes"] = {"new": name}
        return ret
    created = __salt__["vcf_vim_host_datastore.create_vmfs"](
        host, name, device_path, vmfs_version=vmfs_version, profile=profile
    )
    ret["changes"] = {"new": created}
    ret["comment"] = f"Created VMFS{vmfs_version} datastore {name!r} on {host}."
    return ret


def nfs_mounted(
    name,
    host,
    remote_host,
    remote_path,
    access_mode="readWrite",
    ds_type="NFS",
    profile=None,
):
    """
    Ensure an NFS export is mounted as *name* on *host*.

    :param name: Datastore label.
    :param host: ESXi host FQDN, IP, or MOID.
    :param remote_host: NFS server hostname or IP.
    :param remote_path: Exported path on the NFS server.
    :param access_mode: ``readWrite`` (default) or ``readOnly``.
    :param ds_type: ``NFS`` (NFSv3) or ``NFS41``.
    :param profile: Optional pillar profile override.
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    existing = _find(host, name, profile)
    if existing:
        ret["comment"] = f"Datastore {name!r} already mounted on {host}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = (
            f"Would mount {remote_host}:{remote_path} as {name!r} ({ds_type}) on {host}."
        )
        ret["changes"] = {"new": name}
        return ret
    mounted = __salt__["vcf_vim_host_datastore.mount_nfs"](
        host,
        name,
        remote_host,
        remote_path,
        access_mode=access_mode,
        ds_type=ds_type,
        profile=profile,
    )
    ret["changes"] = {"new": mounted}
    ret["comment"] = f"Mounted {remote_host}:{remote_path} as {name!r} on {host}."
    return ret


def absent(name, host, profile=None):
    """Ensure the datastore *name* is not present on *host*."""
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    existing = _find(host, name, profile)
    if not existing:
        ret["comment"] = f"Datastore {name!r} already absent from {host}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Would remove datastore {name!r} from {host}."
        ret["changes"] = {"old": existing}
        return ret
    __salt__["vcf_vim_host_datastore.remove"](host, name, profile=profile)
    ret["changes"] = {"old": existing}
    ret["comment"] = f"Removed datastore {name!r} from {host}."
    return ret
