"""State module for ESXi power-management policy."""

from saltext.vmware.clients import vim_host_powermgmt as c

__virtualname__ = "vmware_vim_host_powermgmt"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def policy(name, host=None, policy_key=None, short_name=None, profile=None):
    """Ensure the active power policy matches the requested key or short name.

    *host* defaults to *name*. Pass exactly one of *policy_key* (int) or
    *short_name* (e.g. ``static``, ``dynamic``, ``low``, ``custom``).
    """
    host = host or name
    ret = _ret(name)
    if policy_key is None and short_name is None:
        ret["result"] = False
        ret["comment"] = "one of policy_key or short_name is required"
        return ret
    current = c.get_policy(__opts__, host, profile=profile)
    if policy_key is not None:
        desired_key = int(policy_key)
    else:
        policies = c.list_policies(__opts__, host, profile=profile)
        match = next((p for p in policies if p["short_name"] == short_name), None)
        if match is None:
            ret["result"] = False
            ret["comment"] = f"no power policy with short_name={short_name!r} on {host}"
            return ret
        desired_key = match["key"]
    if current["key"] == desired_key:
        ret["comment"] = f"power policy on {host} already {current['short_name']!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = (
            f"power policy on {host} would change from {current['key']} to {desired_key}"
        )
        return ret
    new = c.set_policy(__opts__, host, desired_key, profile=profile)
    ret["changes"] = {"policy_key": (current["key"], new["key"])}
    ret["comment"] = f"power policy on {host} set to {new['short_name']!r}"
    return ret
