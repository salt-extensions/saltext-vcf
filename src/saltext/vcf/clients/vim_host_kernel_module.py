"""ESXi kernel-module config via ``HostKernelModuleSystem`` (SOAP)."""

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


def _km(host):
    km = host.configManager.kernelModuleSystem
    if km is None:
        raise RuntimeError(f"host {host.name!r} has no kernelModuleSystem manager")
    return km


def list_(opts, host, profile=None):
    """Return ``[{name, version, modules_dependent, enabled, use_count, loaded, options}, ...]``.

    *modules_dependent* is best-effort — older ESXi builds omit it.
    """
    h = _host(opts, host, profile=profile)
    km = _km(h)
    out = []
    for m in km.QueryModules():
        out.append(
            {
                "name": m.name,
                "version": getattr(m, "version", None),
                "modules_dependent": list(getattr(m, "modulesDependent", None) or []),
                "enabled": bool(getattr(m, "enabled", False)),
                "use_count": int(getattr(m, "useCount", 0)),
                "loaded": bool(getattr(m, "loaded", False)),
            }
        )
    return out


def get_options(opts, host, module, profile=None):
    """Return the configured module-option string for *module*."""
    h = _host(opts, host, profile=profile)
    return _km(h).QueryConfiguredModuleOptionString(name=module)


def set_options(opts, host, module, options, profile=None):
    """Set the kernel module option string. Persisted across reboots."""
    h = _host(opts, host, profile=profile)
    _km(h).UpdateModuleOptionString(name=module, options=options)
    return {"name": module, "options": options}
