"""ESXi firewall rules via SOAP/pyVmomi."""

from pyVmomi import vim

from saltext.vcf.utils import esxi


def _ruleset_to_dict(rs):
    allowed = rs.allowedHosts
    return {
        "key": rs.key,
        "label": rs.label,
        "enabled": rs.enabled,
        "allowed_hosts": {
            "all_ip": getattr(allowed, "allIp", True) if allowed else True,
            "ip_addresses": list(getattr(allowed, "ipAddress", []) or []),
        },
    }


def _find_ruleset(fw_system, rule):
    for rs in fw_system.firewallInfo.ruleset:
        if rs.key == rule:
            return rs
    raise KeyError(f"Firewall rule {rule!r} not found on this host")


def list_(opts, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    fw = host.configManager.firewallSystem
    return {rs.key: _ruleset_to_dict(rs) for rs in fw.firewallInfo.ruleset}


def get(opts, rule, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    rs = _find_ruleset(host.configManager.firewallSystem, rule)
    return _ruleset_to_dict(rs)


def get_or_none(opts, rule, profile=None):
    try:
        return get(opts, rule, profile=profile)
    except KeyError:
        return None


def set_enabled(opts, rule, enabled, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    fw = host.configManager.firewallSystem
    if enabled:
        fw.EnableRuleset(id=rule)
    else:
        fw.DisableRuleset(id=rule)
    return get(opts, rule, profile=profile)


def enabled(opts, profile=None):
    """Return the host's global firewall enabled state (bool)."""
    host = esxi.get_host_system(opts, profile=profile)
    return bool(host.configManager.firewallSystem.firewallInfo.defaultPolicy.incomingBlocked)


def set_global_enabled(opts, enabled, profile=None):
    """Enable or disable the host firewall globally.

    Wraps ``HostFirewallSystem.UpdateDefaultPolicy``.  When
    ``enabled=False``, both ``incomingBlocked`` and
    ``outgoingBlocked`` flip to False, allowing all traffic
    regardless of ruleset state.  This is the ESXi-equivalent
    of ``esxcli network firewall set --enabled=false``.
    """
    host = esxi.get_host_system(opts, profile=profile)
    fw = host.configManager.firewallSystem
    policy = vim.host.FirewallInfo.DefaultPolicy(
        incomingBlocked=bool(enabled),
        outgoingBlocked=bool(enabled),
    )
    fw.UpdateDefaultPolicy(defaultPolicy=policy)
    return bool(host.configManager.firewallSystem.firewallInfo.defaultPolicy.incomingBlocked)


def set_allowed_ips(opts, rule, allowed_ips, all_ip=False, profile=None):
    """Replace the allowed-IP list for *rule*.

    *allowed_ips* is a list of strings (CIDR or single addresses).
    *all_ip* True opens the rule to all sources.
    """
    host = esxi.get_host_system(opts, profile=profile)
    fw = host.configManager.firewallSystem
    spec = vim.host.Ruleset.RulesetSpec(
        allowedHosts=vim.host.Ruleset.IpList(
            allIp=bool(all_ip),
            ipAddress=list(allowed_ips),
        )
    )
    fw.UpdateRuleset(id=rule, spec=spec)
    return get(opts, rule, profile=profile)
