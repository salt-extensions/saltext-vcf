"""State module for ESXi SNMP agent."""

from saltext.vmware.clients import vim_host_snmp as c

__virtualname__ = "vmware_vim_host_snmp"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def config(
    name,
    host=None,
    enabled=None,
    port=None,
    read_only_communities=None,
    trap_targets=None,
    profile=None,
):
    """Ensure SNMP config on *host* matches the supplied fields.

    None values are not checked. *trap_targets* compared by sorted JSON-stable form.
    """
    host = host or name
    ret = _ret(name)
    current = c.get(__opts__, host, profile=profile)
    drift = {}
    if enabled is not None and bool(current["enabled"]) != bool(enabled):
        drift["enabled"] = (current["enabled"], bool(enabled))
    if port is not None and int(current.get("port") or 0) != int(port):
        drift["port"] = (current.get("port"), int(port))
    if read_only_communities is not None and sorted(
        current.get("read_only_communities") or []
    ) != sorted(read_only_communities):
        drift["read_only_communities"] = (
            current.get("read_only_communities"),
            list(read_only_communities),
        )
    if trap_targets is not None:
        cur = sorted(
            (t["host"], int(t["port"]), t["community"]) for t in current.get("trap_targets") or []
        )
        des = sorted((t["host"], int(t["port"]), t["community"]) for t in trap_targets)
        if cur != des:
            drift["trap_targets"] = (current.get("trap_targets"), list(trap_targets))
    if not drift:
        ret["comment"] = f"SNMP on {host} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"SNMP on {host} would change: {sorted(drift)}"
        return ret
    c.set_(
        __opts__,
        host,
        enabled=enabled,
        port=port,
        read_only_communities=read_only_communities,
        trap_targets=trap_targets,
        profile=profile,
    )
    ret["changes"] = drift
    ret["comment"] = f"SNMP on {host} updated"
    return ret
