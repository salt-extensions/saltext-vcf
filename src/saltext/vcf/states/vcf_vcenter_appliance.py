"""State module for vCenter appliance configuration."""

from saltext.vcf.clients import vcenter_appliance as c

__virtualname__ = "vcf_vcenter_appliance"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def dns_servers(name, servers, mode="is_static", profile=None):
    """Ensure the appliance's DNS server list and mode match *servers* / *mode*.

    *name* is descriptive. *mode* is ``"is_static"`` or ``"dhcp"``.
    """
    ret = _ret(name)
    current = c.dns_get(__opts__, profile=profile) or {}
    current_servers = sorted(current.get("servers") or [])
    desired_servers = sorted(servers)

    actions = []
    changes = {}
    if current.get("mode") != mode:
        actions.append(f"mode={mode}")
        changes["mode"] = {"old": current.get("mode"), "new": mode}
    if current_servers != desired_servers:
        actions.append("servers")
        changes["servers"] = {"old": current_servers, "new": desired_servers}

    if not actions:
        ret["comment"] = "DNS already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DNS would change: {', '.join(actions)}"
        return ret
    c.dns_set(__opts__, servers, mode=mode, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"DNS updated: {', '.join(actions)}"
    return ret


def logging_forwarding(name, servers, profile=None):
    """Ensure the appliance's syslog forwarding destinations match *servers*.

    *servers* is a list of dicts like
    ``{"hostname": "...", "port": 514, "protocol": "UDP"}``.
    """
    ret = _ret(name)
    current = c.logging_forwarding_get(__opts__, profile=profile) or []
    # The list returned has a "cfg_list" key wrapper in some vCenter releases.
    if isinstance(current, dict):
        current = current.get("cfg_list") or current.get("value") or []

    def _key(entry):
        return (entry.get("hostname"), entry.get("port"), entry.get("protocol"))

    current_sorted = sorted(current, key=_key)
    desired_sorted = sorted(servers, key=_key)

    if current_sorted == desired_sorted:
        ret["comment"] = "Syslog forwarding already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "Syslog forwarding would be updated"
        return ret
    c.logging_forwarding_set(__opts__, servers, profile=profile)
    ret["changes"] = {"forwarders": {"old": current, "new": list(servers)}}
    ret["comment"] = "Syslog forwarding updated"
    return ret


def _current_ceip_accepted(profile=None):
    """Read CEIP status, tolerating both bare and value-wrapped response shapes."""
    current = c.ceip_get(__opts__, profile=profile) or {}
    if isinstance(current, dict) and "accepted" not in current and "value" in current:
        current = current["value"] or {}
    return bool(current.get("accepted")) if isinstance(current, dict) else False


def ceip_set(name, accepted, profile=None):
    """Ensure CEIP participation matches *accepted*.

    *name* is descriptive. Set *accepted* to ``False`` to opt the vCenter
    out of the Customer Experience Improvement Program (912 controls / STIG).
    """
    ret = _ret(name)
    desired = bool(accepted)
    current = _current_ceip_accepted(profile=profile)

    if current == desired:
        ret["comment"] = f"CEIP already accepted={desired}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"CEIP would change accepted: {current} -> {desired}"
        return ret
    c.ceip_set(__opts__, desired, profile=profile)
    ret["changes"] = {"accepted": {"old": current, "new": desired}}
    ret["comment"] = f"CEIP updated to accepted={desired}"
    return ret


def ceip_disabled(name, profile=None):
    """Ensure CEIP participation is disabled (``accepted=False``).

    Thin wrapper around :func:`ceip_set` for the common compliance case.
    """
    return ceip_set(name, accepted=False, profile=profile)
