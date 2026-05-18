"""State module for ESXi firewall rules."""

from saltext.vcf.clients import esxi_firewall as c

__virtualname__ = "vcf_esxi_firewall"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def rule_enabled(name, enabled=True, allowed_ips=None, all_ip=None, profile=None):
    """Ensure firewall rule *name* matches the desired enabled / allowed-IP state.

    *allowed_ips* and *all_ip* are optional — when omitted the allowed-host
    portion is left untouched.
    """
    ret = _ret(name)
    rule = c.get_or_none(__opts__, name, profile=profile)
    if rule is None:
        ret["result"] = False
        ret["comment"] = f"Rule {name} not found"
        return ret

    actions = []
    changes = {}
    if rule.get("enabled") != bool(enabled):
        actions.append(f"enabled={enabled}")
        changes["enabled"] = {"old": rule.get("enabled"), "new": bool(enabled)}

    current_hosts = rule.get("allowed_hosts") or {}
    if allowed_ips is not None or all_ip is not None:
        desired_all = bool(all_ip if all_ip is not None else current_hosts.get("all_ip", False))
        desired_ips = (
            list(allowed_ips)
            if allowed_ips is not None
            else list(current_hosts.get("ip_addresses") or [])
        )
        current_all = bool(current_hosts.get("all_ip", False))
        current_ips = list(current_hosts.get("ip_addresses") or [])
        if current_all != desired_all or sorted(current_ips) != sorted(desired_ips):
            actions.append("allowed_hosts")
            changes["allowed_hosts"] = {
                "old": {"all_ip": current_all, "ip_addresses": current_ips},
                "new": {"all_ip": desired_all, "ip_addresses": desired_ips},
            }

    if not actions:
        ret["comment"] = f"Rule {name} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Rule {name} would change: {', '.join(actions)}"
        return ret
    if "enabled=" + str(enabled) in actions or any(a.startswith("enabled=") for a in actions):
        c.set_enabled(__opts__, name, enabled, profile=profile)
    if "allowed_hosts" in actions:
        c.set_allowed_ips(
            __opts__,
            name,
            changes["allowed_hosts"]["new"]["ip_addresses"],
            all_ip=changes["allowed_hosts"]["new"]["all_ip"],
            profile=profile,
        )
    ret["changes"] = changes
    ret["comment"] = f"Rule {name} updated: {', '.join(actions)}"
    return ret


def rule_disabled(name, profile=None):
    """Shortcut for ``rule_enabled(name, enabled=False)``."""
    return rule_enabled(name, enabled=False, profile=profile)
