"""ESXi storage HBA + VMFS rescan and refresh via ``HostStorageSystem``."""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


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


def _ss(host):
    s = host.configManager.storageSystem
    if s is None:
        raise RuntimeError(f"host {host.name!r} has no storageSystem manager")
    return s


def rescan_all_hba(opts, host, profile=None):
    """Synchronously rescan all HBAs on *host*."""
    _ss(_host(opts, host, profile=profile)).RescanAllHba()
    return True


def rescan_vmfs(opts, host, profile=None):
    """Rescan for new VMFS volumes."""
    _ss(_host(opts, host, profile=profile)).RescanVmfs()
    return True


def refresh(opts, host, profile=None):
    """Re-read the storage system state from the host."""
    _ss(_host(opts, host, profile=profile)).RefreshStorageSystem()
    return True


# ---------------------------------------------------------------------------
# SCSI LUN inventory + attach/detach (vmware_esxi.list_scsi_luns parity)
# ---------------------------------------------------------------------------

_STATE_MAP = {
    "attached": "ok",
    "detached": "off",
    "ok": "attached",
    "off": "detached",
}


def _lun_to_dict(lun):
    descriptor = [
        (d.id, d.quality) for d in (getattr(lun, "descriptor", None) or []) if d.quality == "highQuality"
    ]
    return {
        "name": lun.displayName,
        "canonical_name": getattr(lun, "canonicalName", None),
        "path": lun.devicePath,
        "device": lun.deviceName,
        "uuid": getattr(lun, "uuid", None),
        "state": _STATE_MAP.get(lun.operationalState[0], str(lun.operationalState[0])),
        "descriptor": descriptor,
        "local": bool(getattr(lun, "localDisk", False)),
        "ssd": bool(getattr(lun, "ssd", False)),
        "location": getattr(lun, "physicalLocation", None),
    }


def scsi_luns(opts, host, *, lun_name=None, state=None, disk_ids=None, scsi_addresses=None,
              ssd=None, profile=None):
    """List SCSI LUNs on *host* with full detail and optional filters.

    Filters:

    * *lun_name* — substring match on ``devicePath``.
    * *state* — ``attached`` | ``detached``.
    * *disk_ids* / *scsi_addresses* — match canonical name / scsi address.
    * *ssd* — ``True`` (SSD only) / ``False`` (non-SSD only).
    """
    storage = _ss(_host(opts, host, profile=profile))
    luns = storage.storageDeviceInfo.scsiLun or []
    out = []
    for lun in luns:
        d = _lun_to_dict(lun)
        if lun_name and lun_name not in d["path"]:
            continue
        if state and d["state"] != state:
            continue
        if disk_ids and d["canonical_name"] not in list(disk_ids):
            continue
        if scsi_addresses and d["path"] not in list(scsi_addresses):
            continue
        if ssd is not None and d["ssd"] != bool(ssd):
            continue
        out.append(d)
    return out


def attach_lun(opts, host, lun_canonical_name, profile=None):
    """Attach a SCSI LUN (``HostStorageSystem.AttachScsiLun``). Idempotent."""
    storage = _ss(_host(opts, host, profile=profile))
    try:
        storage.AttachScsiLun(lunCanonicalName=lun_canonical_name)
    except vim.fault.InvalidState:
        # already attached — treat as no-op
        pass
    storage.RefreshStorageSystem()
    return True


def detach_lun(opts, host, lun_canonical_name, profile=None):
    """Detach a SCSI LUN (``HostStorageSystem.DetachScsiLun``). Idempotent."""
    storage = _ss(_host(opts, host, profile=profile))
    try:
        storage.DetachScsiLun(lunCanonicalName=lun_canonical_name)
    except vim.fault.NotFound:
        pass
    storage.RefreshStorageSystem()
    return True
