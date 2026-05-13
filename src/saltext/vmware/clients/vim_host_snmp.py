"""ESXi SNMP agent config via ``HostSnmpSystem``."""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


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


def _snmp(host):
    s = host.configManager.snmpSystem
    if s is None:
        raise RuntimeError(f"host {host.name!r} has no snmpSystem manager")
    return s


def _to_dict(cfg):
    return {
        "enabled": bool(cfg.enabled),
        "port": int(cfg.port) if cfg.port is not None else None,
        "read_only_communities": list(cfg.readOnlyCommunities or []),
        "trap_targets": [
            {"host": t.hostName, "port": int(t.port), "community": t.community}
            for t in (cfg.trapTargets or [])
        ],
        "options": {o.key: o.value for o in (cfg.option or [])},
    }


def get(opts, host, profile=None):
    return _to_dict(_snmp(_host(opts, host, profile=profile)).configuration)


def set_(
    opts,
    host,
    *,
    enabled=None,
    port=None,
    read_only_communities=None,
    trap_targets=None,
    profile=None,
):
    """Reconfigure the SNMP agent. Each None argument is left alone.

    *trap_targets* — list of ``{host, port, community}`` dicts.
    """
    snmp = _snmp(_host(opts, host, profile=profile))
    cur = snmp.configuration
    spec = vim.host.SnmpSystem.SnmpConfigSpec()
    spec.enabled = bool(cur.enabled) if enabled is None else bool(enabled)
    spec.port = int(cur.port) if port is None else int(port)
    spec.readOnlyCommunities = (
        list(cur.readOnlyCommunities or [])
        if read_only_communities is None
        else list(read_only_communities)
    )
    if trap_targets is not None:
        spec.trapTargets = [
            vim.host.SnmpSystem.SnmpConfigSpec.SnmpTrapTarget(
                hostName=t["host"], port=int(t["port"]), community=t["community"]
            )
            for t in trap_targets
        ]
    else:
        spec.trapTargets = list(cur.trapTargets or [])
    snmp.ReconfigureSnmpAgent(spec=spec)
    return get(opts, host, profile=profile)
