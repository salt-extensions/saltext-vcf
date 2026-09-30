"""ESXi firewall rulesets via ``HostFirewallSystem`` (vCenter-routed SOAP).

Port of ``vmware_esxi.get_firewall_config`` / ``set_firewall_config``.
The standalone-ESXi variant lives in :mod:`saltext.vcf.clients.esxi_firewall`;
this client covers hosts managed by vCenter where the direct REST
surface is locked. Supports the full ``vim.host.Ruleset.RulesetSpec``
shape, including ``ipNetwork`` allow-lists.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _resolve(opts, host, profile=None):
    return soap.resolve_host_system(opts, host, profile=profile)


def _firewall_system(opts, host, profile=None):
    h = _resolve(opts, host, profile=profile)
    fw = h.configManager.firewallSystem
    if fw is None:
        raise RuntimeError(f"host {host!r} has no firewallSystem manager")
    return h, fw


def _ruleset_to_dict(ruleset):
    allowed = ruleset.allowedHosts
    return {
        "name": ruleset.key,
        "service": ruleset.service,
        "enabled": bool(ruleset.enabled),
        "allowed_hosts": {
            "all_ip": bool(allowed.allIp),
            "ip_address": list(allowed.ipAddress or []),
            "ip_network": [
                f"{n.network}/{n.prefixLength}" for n in (allowed.ipNetwork or [])
            ],
        },
        "rule": [
            {
                "port": r.port,
                "end_port": r.endPort,
                "direction": r.direction,
                "port_type": r.portType,
                "protocol": r.protocol,
            }
            for r in (ruleset.rule or [])
        ],
    }


def get_all(opts, host, profile=None):
    """Return all firewall rulesets on *host* as ``{name: ruleset-dict}``."""
    _h, fw = _firewall_system(opts, host, profile=profile)
    return {r.key: _ruleset_to_dict(r) for r in (fw.firewallInfo.ruleset or [])}


def get(opts, host, ruleset_name, profile=None):
    """Return one ruleset by name (raises ``LookupError`` when missing)."""
    _h, fw = _firewall_system(opts, host, profile=profile)
    for ruleset in fw.firewallInfo.ruleset or []:
        if ruleset.key == ruleset_name:
            return _ruleset_to_dict(ruleset)
    raise LookupError(f"firewall ruleset {ruleset_name!r} not found on {host!r}")


def get_or_none(opts, host, ruleset_name, profile=None):
    try:
        return get(opts, host, ruleset_name, profile=profile)
    except LookupError:
        return None


def set_enabled(opts, host, ruleset_name, enabled, profile=None):
    """Enable or disable a single ruleset. Returns the new enabled state."""
    _h, fw = _firewall_system(opts, host, profile=profile)
    if enabled:
        fw.EnableRuleset(id=ruleset_name)
    else:
        fw.DisableRuleset(id=ruleset_name)
    return bool(enabled)


def set_config(opts, host, firewall_config, profile=None):
    """Apply a ``vmware_esxi.set_firewall_config``-shaped dict to *host*.

    Shape::

        {"name": "CIMHttpServer", "enabled": true,
         "allowed_hosts": {"all_ip": false, "ip_address": [...],
                           "ip_network": ["10.0.0.0/8"]}}

    Uses ``vim.host.Ruleset.IpList`` (declares ``allIp``,
    ``ipAddress`` and ``ipNetwork``).
    """
    _h, fw = _firewall_system(opts, host, profile=profile)
    name = firewall_config["name"]
    if firewall_config.get("enabled"):
        fw.EnableRuleset(id=name)
    else:
        fw.DisableRuleset(id=name)
    if "allowed_hosts" in firewall_config:
        allowed = firewall_config["allowed_hosts"]
        spec = vim.host.Ruleset.RulesetSpec()
        spec.allowedHosts = vim.host.Ruleset.IpList()
        spec.allowedHosts.allIp = bool(allowed.get("all_ip", False))
        spec.allowedHosts.ipAddress = list(allowed.get("ip_address", []) or [])
        spec.allowedHosts.ipNetwork = [
            vim.host.Ruleset.IpNetwork(
                network=n.split("/")[0], prefixLength=int(n.split("/")[1])
            )
            for n in (allowed.get("ip_network", []) or [])
        ]
        fw.UpdateRuleset(id=name, spec=spec)
    return get(opts, host, name, profile=profile)


def set_all_configs(opts, host, firewall_configs, profile=None):
    """Apply a list of rule-config dicts (``set_all_firewall_configs`` parity)."""
    out = []
    for cfg in firewall_configs:
        out.append(set_config(opts, host, cfg, profile=profile))
    return out


def set_allowed(
    opts,
    host,
    ruleset_name,
    *,
    allowed_ips=None,
    ip_networks=None,
    all_ip=None,
    enabled=None,
    profile=None,
):
    """Update a ruleset's allow-list (IPs, networks, all-IP) and enabled state.

    Builds ``vim.host.Ruleset.RulesetSpec`` with
    ``vim.host.Ruleset.IpList`` (``allIp``, ``ipAddress``, ``ipNetwork`` —
    the real class; there is no ``AllowedHostList`` in vim25). The
    enabled state is applied separately via ``EnableRuleset`` /
    ``DisableRuleset``. Only the provided fields are changed; the other
    properties are preserved by re-sending the current values.
    """
    _h, fw = _firewall_system(opts, host, profile=profile)
    current = get(opts, host, ruleset_name, profile=profile)
    if enabled is not None:
        set_enabled(opts, host, ruleset_name, enabled, profile=profile)
    spec = vim.host.Ruleset.RulesetSpec()
    spec.allowedHosts = vim.host.Ruleset.IpList(
        allIp=bool(current["allowed_hosts"]["all_ip"]) if all_ip is None else bool(all_ip),
        ipAddress=list(current["allowed_hosts"]["ip_address"]) if allowed_ips is None else list(allowed_ips),
        ipNetwork=[
            vim.host.Ruleset.IpNetwork(network=n.split("/")[0], prefixLength=int(n.split("/")[1]))
            for n in (
                current["allowed_hosts"]["ip_network"] if ip_networks is None else ip_networks
            )
        ],
    )
    fw.UpdateRuleset(id=ruleset_name, spec=spec)
    return get(opts, host, ruleset_name, profile=profile)
