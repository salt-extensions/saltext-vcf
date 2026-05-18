"""ESXi PCI passthrough config via ``HostPciPassthruSystem`` (SOAP).

Changes typically require a host reboot to take effect; the returned dict
exposes ``reboot_required`` from the device's current state.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for host in container.view:
            if host_id_or_name in (host._moId, host.name):  # noqa: SLF001
                return host
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


def _pci(host):
    sys_ = host.configManager.pciPassthruSystem
    if sys_ is None:
        raise RuntimeError(f"host {host.name!r} has no pciPassthruSystem manager")
    return sys_


def refresh(opts, host, profile=None):
    """Force the host to re-scan its PCI inventory."""
    h = _host(opts, host, profile=profile)
    _pci(h).Refresh()


def list_(opts, host, profile=None):
    """Return ``[{id, vendor_id, device_id, vendor_name, device_name,
    passthru_capable, passthru_enabled, passthru_active, dependent_device,
    reboot_required}, ...]``.
    """
    h = _host(opts, host, profile=profile)
    out = []
    for dev in _pci(h).pciPassthruInfo or []:
        out.append(
            {
                "id": dev.id,
                "vendor_id": getattr(dev, "vendorId", None),
                "device_id": getattr(dev, "deviceId", None),
                "vendor_name": getattr(dev, "vendorName", None),
                "device_name": getattr(dev, "deviceName", None),
                "passthru_capable": bool(getattr(dev, "passthruCapable", False)),
                "passthru_enabled": bool(getattr(dev, "passthruEnabled", False)),
                "passthru_active": bool(getattr(dev, "passthruActive", False)),
                "dependent_device": getattr(dev, "dependentDevice", None),
                "reboot_required": bool(
                    getattr(dev, "passthruEnabled", False) != getattr(dev, "passthruActive", False)
                ),
            }
        )
    return out


def set_enabled(opts, host, pci_id, enabled, profile=None):
    """Toggle passthrough on a single PCI device. Returns ``{id, enabled, reboot_required: True}``."""
    h = _host(opts, host, profile=profile)
    config = vim.host.PciPassthruConfig(id=pci_id, passthruEnabled=bool(enabled))
    _pci(h).UpdatePassthruConfig([config])
    return {"id": pci_id, "enabled": bool(enabled), "reboot_required": True}
