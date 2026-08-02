"""State module for vRLI appliance settings (session timeout + DNS).

Both operations require SSH — the vRLI 9.0.2.0 REST API has no
write surface for either control. See
:mod:`saltext.vcf.clients.vrli_settings` for the file paths edited.
"""

from saltext.vcf.clients import vrli_settings as c

__virtualname__ = "vcf_vrli_settings"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def session_timeout_configured(name, seconds=1800, profile=None):
    """Ensure the appliance session inactivity timeout is *seconds*.

    Default 1800 s (30 min) matches the 912 Controls requirement. The
    value is stored on the appliance in *minutes* (rounded down).
    Restarts the ``loginsight`` service on change.
    """
    ret = _ret(name)
    current = c.get_session_timeout(__opts__, profile=profile)
    desired = (int(seconds) // 60) * 60  # normalize to minute boundary
    if current == desired:
        ret["comment"] = f"Session timeout already {desired}s"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = (
            f"Session timeout would be changed from {current}s to {desired}s "
            f"(loginsight would restart)"
        )
        return ret
    c.set_session_timeout(__opts__, seconds, profile=profile)
    ret["changes"] = {"session_timeout_seconds": {"old": current, "new": desired}}
    ret["comment"] = f"Session timeout set to {desired}s; loginsight restart requested"
    return ret


def dns_servers_configured(name, servers, profile=None):
    """Ensure the IPv4 DNS server list matches *servers* (order-insensitive).

    Reads the on-appliance state via SSH (``10-eth0.network``) rather
    than the REST cluster-nodes view, because the REST view can lag a
    write by several seconds while ``systemd-resolved`` recomputes.
    """
    ret = _ret(name)
    desired = list(servers)
    current = c.get_dns_servers_from_appliance(__opts__, profile=profile)
    if set(current) == set(desired):
        ret["comment"] = f"DNS servers already set to {sorted(desired)}"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"DNS servers would be set to {desired} (was {current})"
        return ret
    c.set_dns_servers(__opts__, desired, profile=profile)
    ret["changes"] = {"dns_servers": {"old": current, "new": desired}}
    ret["comment"] = f"DNS servers set to {desired}"
    return ret
