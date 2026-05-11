"""State module for ESXi syslog configuration."""

from saltext.vmware.clients import esxi_syslog as c

__virtualname__ = "vmware_esxi_syslog"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def servers(name, servers, log_level=None, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure remote syslog destinations and optional log level match."""
    ret = _ret(name)
    current = c.get(__opts__, profile=profile) or {}
    current_servers = sorted(current.get("servers") or [])
    desired_servers = sorted(servers)

    actions = []
    changes = {}
    if current_servers != desired_servers:
        actions.append("servers")
        changes["servers"] = {"old": current_servers, "new": desired_servers}
    if log_level is not None and current.get("log_level") != log_level:
        actions.append(f"log_level={log_level}")
        changes["log_level"] = {"old": current.get("log_level"), "new": log_level}

    if not actions:
        ret["comment"] = "Syslog already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Syslog would change: {', '.join(actions)}"
        return ret
    if "servers" in actions:
        c.set_servers(__opts__, servers, profile=profile)
    if log_level is not None and current.get("log_level") != log_level:
        c.set_log_level(__opts__, log_level, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"Syslog updated: {', '.join(actions)}"
    return ret
