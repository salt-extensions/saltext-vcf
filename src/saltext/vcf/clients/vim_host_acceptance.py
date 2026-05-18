"""ESXi VIB acceptance level (community/partner/vmware-accepted/vmware-certified)."""

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


def _icm(host):
    icm = host.configManager.imageConfigManager
    if icm is None:
        raise RuntimeError(f"host {host.name!r} has no imageConfigManager")
    return icm


def get(opts, host, profile=None):
    """Return the host's current acceptance level string."""
    return _icm(_host(opts, host, profile=profile)).HostImageConfigGetAcceptance()


def set_(opts, host, level, profile=None):
    """Set the host's acceptance level.

    *level* — ``community``, ``partner``, ``vmware_accepted``, ``vmware_certified``.
    """
    _icm(_host(opts, host, profile=profile)).HostImageConfigSetAcceptance(newAcceptanceLevel=level)
    return level
