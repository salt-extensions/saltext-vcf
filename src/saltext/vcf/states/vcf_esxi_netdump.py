"""State module for ESXi network coredump (netdump)."""

from saltext.vcf.clients import esxi_netdump as c

__virtualname__ = "vcf_esxi_netdump"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def configured(name, interface_name, server_ip, server_port, enabled=True, profile=None):
    """Ensure network coredump is configured to collect to *server_ip*:*server_port*
    over *interface_name*, and enabled/disabled per *enabled*.

    *name* is descriptive only.
    """
    ret = _ret(name)
    current = c.get(__opts__, profile=profile)
    wanted = {
        "interface_name": interface_name,
        "server_ip": server_ip,
        "server_port": server_port,
        "enabled": bool(enabled),
    }
    diff = {k: v for k, v in wanted.items() if current.get(k) != v}
    if not diff:
        ret["comment"] = "netdump already configured as desired"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"netdump would change: {diff}"
        return ret

    network_changed = any(k in diff for k in ("interface_name", "server_ip", "server_port"))
    if network_changed:
        c.set_network(__opts__, interface_name, server_ip, server_port, profile=profile)
    if "enabled" in diff:
        c.set_enabled(__opts__, enabled, profile=profile)

    ret["changes"] = {k: {"old": current.get(k), "new": v} for k, v in diff.items()}
    ret["comment"] = "netdump configuration updated"
    return ret
