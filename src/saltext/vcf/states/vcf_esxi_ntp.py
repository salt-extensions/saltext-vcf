"""State module for ESXi NTP configuration."""

from saltext.vcf.clients import esxi_ntp as c

__virtualname__ = "vcf_esxi_ntp"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def servers(name, servers, enabled=True, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure NTP is configured with the exact server list, in any order.

    *name* is descriptive. *enabled* controls whether the NTP service should
    be running according to the configuration object.
    """
    ret = _ret(name)
    current = c.get(__opts__, profile=profile) or {}
    current_servers = sorted(current.get("servers") or [])
    desired_servers = sorted(servers)

    actions = []
    changes = {}
    if current_servers != desired_servers:
        actions.append("servers")
        changes["servers"] = {"old": current_servers, "new": desired_servers}
    if current.get("enabled") != bool(enabled):
        actions.append(f"enabled={enabled}")
        changes["enabled"] = {"old": current.get("enabled"), "new": bool(enabled)}

    if not actions:
        ret["comment"] = "NTP already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"NTP would change: {', '.join(actions)}"
        return ret
    if "servers" in actions:
        c.set_servers(__opts__, servers, profile=profile)
    if any(a.startswith("enabled=") for a in actions):
        c.set_enabled(__opts__, enabled, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"NTP updated: {', '.join(actions)}"
    return ret
