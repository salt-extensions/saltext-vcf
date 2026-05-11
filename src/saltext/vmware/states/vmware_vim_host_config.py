"""State module for vCenter-managed ESXi host config."""

from saltext.vmware.clients import vim_host_config as c

__virtualname__ = "vmware_vim_host_config"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def ntp(name, host=None, servers=None, running=None, policy=None, profile=None):
    """Ensure NTP servers, running state, and policy match the desired values.

    *name* is informational; *host* defaults to *name* when omitted.
    Any of *servers*, *running*, *policy* left as ``None`` is not checked.
    """
    host = host or name
    ret = _ret(name)
    current = c.ntp_get(__opts__, host, profile=profile)
    drift = {}
    if servers is not None and sorted(current["servers"]) != sorted(servers):
        drift["servers"] = (current["servers"], list(servers))
    if running is not None and current["enabled"] != bool(running):
        drift["running"] = (current["enabled"], bool(running))
    if policy is not None and current["policy"] != policy:
        drift["policy"] = (current["policy"], policy)
    if not drift:
        ret["comment"] = f"NTP on {host} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"NTP on {host} would be updated: {sorted(drift)}"
        return ret
    if "servers" in drift:
        c.ntp_set_servers(__opts__, host, list(servers), profile=profile)
    if "running" in drift:
        c.ntp_set_running(__opts__, host, bool(running), profile=profile)
    if "policy" in drift:
        c.ntp_set_policy(__opts__, host, policy, profile=profile)
    ret["changes"] = drift
    ret["comment"] = f"NTP on {host} updated"
    return ret


def service(name, host=None, service_id=None, running=None, policy=None, profile=None):
    """Ensure a generic ESXi service is in the desired running/policy state."""
    host = host or name
    service_id = service_id or name
    ret = _ret(name)
    services = c.service_list(__opts__, host, profile=profile)
    current = next((s for s in services if s["key"] == service_id), None)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"service {service_id} not found on {host}"
        return ret
    drift = {}
    if running is not None and current["running"] != bool(running):
        drift["running"] = (current["running"], bool(running))
    if policy is not None and current["policy"] != policy:
        drift["policy"] = (current["policy"], policy)
    if not drift:
        ret["comment"] = f"service {service_id} on {host} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"service {service_id} on {host} would change: {sorted(drift)}"
        return ret
    if "running" in drift:
        if running:
            c.service_start(__opts__, host, service_id, profile=profile)
        else:
            c.service_stop(__opts__, host, service_id, profile=profile)
    if "policy" in drift:
        c.service_set_policy(__opts__, host, service_id, policy, profile=profile)
    ret["changes"] = drift
    ret["comment"] = f"service {service_id} on {host} updated"
    return ret


def advanced_setting(name, host=None, key=None, value=None, profile=None):
    """Ensure an advanced host setting equals *value*."""
    host = host or name
    key = key or name
    ret = _ret(name)
    try:
        current = c.advanced_get(__opts__, host, key=key, profile=profile)
    except LookupError:
        ret["result"] = False
        ret["comment"] = f"advanced setting {key} not found on {host}"
        return ret
    if current == value:
        ret["comment"] = f"{key} on {host} already {value!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{key} on {host} would change from {current!r} to {value!r}"
        return ret
    c.advanced_set(__opts__, host, key, value, profile=profile)
    ret["changes"] = {"value": (current, value)}
    ret["comment"] = f"{key} on {host} set to {value!r}"
    return ret


def ad_joined(
    name, host=None, domain=None, username=None, password=None, ou_path=None, profile=None
):
    """Ensure *host* is joined to AD *domain*."""
    host = host or name
    ret = _ret(name)
    status = c.ad_status(__opts__, host, profile=profile)
    if status["joined"] and status["domain"] == domain:
        ret["comment"] = f"{host} already joined to {domain}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{host} would be joined to {domain}"
        return ret
    c.ad_join(__opts__, host, domain, username, password, ou_path=ou_path, profile=profile)
    ret["changes"] = {"domain": (status["domain"], domain)}
    ret["comment"] = f"{host} joined to {domain}"
    return ret
