"""ESXi hyperthreading config via ``HostCpuSchedulerSystem``."""

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


def _cs(host):
    cs = host.configManager.cpuScheduler
    if cs is None:
        raise RuntimeError(f"host {host.name!r} has no cpuScheduler manager")
    return cs


def get(opts, host, profile=None):
    """Return ``{available, active, config}``. Reboot required to apply config drift."""
    info = _cs(_host(opts, host, profile=profile)).hyperthreadInfo
    return {
        "available": bool(info.available),
        "active": bool(info.active),
        "config": bool(info.config),
    }


def enable(opts, host, profile=None):
    """Mark hyperthreading enabled. Reboot required to take effect."""
    _cs(_host(opts, host, profile=profile)).EnableHyperThreading()
    return True


def disable(opts, host, profile=None):
    """Mark hyperthreading disabled. Reboot required to take effect."""
    _cs(_host(opts, host, profile=profile)).DisableHyperThreading()
    return True
