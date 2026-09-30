"""ESXi installed software packages (VIBs) via ``HostImageConfigManager``.

Port of ``vmware_esxi.list_pkgs`` — ``FetchSoftwarePackages()`` returns
``vim.software.PackageInfo`` records for every VIB on the host.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _resolve(opts, host, profile=None):
    return soap.resolve_host_system(opts, host, profile=profile)


def list_(opts, host, pkg_name=None, profile=None):
    """Return the VIBs installed on *host*, optionally filtered by *pkg_name*.

    Shape per package::

        {"version", "vendor", "summary", "description", "acceptance_level",
         "maintenance_mode_required", "creation_date"}
    """
    h = _resolve(opts, host, profile=profile)
    mgr = h.configManager.imageConfigManager
    if mgr is None:
        raise RuntimeError(f"host {host!r} has no imageConfigManager (pre-7.0 image API)")
    out = {}
    for pkg in mgr.FetchSoftwarePackages() or []:
        if pkg_name and pkg.name != pkg_name:
            continue
        out[pkg.name] = {
            "version": pkg.version,
            "vendor": pkg.vendor,
            "summary": pkg.summary,
            "description": pkg.description,
            "acceptance_level": pkg.acceptanceLevel,
            "maintenance_mode_required": bool(pkg.maintenanceModeRequired),
            "creation_date": (pkg.creationDate.isoformat() if pkg.creationDate else None),
        }
    return out
