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
