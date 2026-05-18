"""ESXi power-management policy via ``HostPowerSystem`` (SOAP).

Policies are vendor/hardware-dependent. Common keys: ``high-performance``,
``balanced``, ``low-power``, ``custom``.
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


def _power(host):
    p = host.configManager.powerSystem
    if p is None:
        raise RuntimeError(f"host {host.name!r} has no powerSystem manager")
    return p


def list_policies(opts, host, profile=None):
    """Return ``[{key, name, short_name, description}, ...]`` from the host's power capabilities."""
    h = _host(opts, host, profile=profile)
    ps = _power(h)
    return [
        {
            "key": int(p.key),
            "name": p.name,
            "short_name": p.shortName,
            "description": p.description,
        }
        for p in (ps.capability.availablePolicy or [])
    ]


def get_policy(opts, host, profile=None):
    """Return ``{key, name, short_name, description}`` for the active policy."""
    h = _host(opts, host, profile=profile)
    info = _power(h).info
    p = info.currentPolicy
    return {
        "key": int(p.key),
        "name": p.name,
        "short_name": p.shortName,
        "description": p.description,
    }


def set_policy(opts, host, policy_key, profile=None):
    """Set the active power policy by integer key."""
    h = _host(opts, host, profile=profile)
    _power(h).ConfigurePowerPolicy(key=int(policy_key))
    return get_policy(opts, host, profile=profile)
