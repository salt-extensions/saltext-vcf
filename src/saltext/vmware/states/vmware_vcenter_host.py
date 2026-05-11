"""State module for vCenter hosts."""

from saltext.vmware.clients import vcenter_host as r

__virtualname__ = "vmware_vcenter_host"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, profile=None):
    """Ensure a host is registered in vCenter (commissioning is owned by SDDC Manager)."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is not None:
        ret["comment"] = f"Host {name} is present in vCenter"
        return ret
    ret["result"] = False
    ret["comment"] = f"Host {name} is not present in vCenter — commission it via SDDC Manager"
    return ret


def absent(name, profile=None):
    """Ensure a host is no longer in vCenter inventory."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Host {name} is already absent from vCenter"
        return ret
    ret["result"] = False
    ret["comment"] = f"Host {name} is still present in vCenter — decommission it via SDDC Manager"
    return ret


def maintenance(name, enabled=True, profile=None):
    """Ensure a host is in (or out of) maintenance mode."""
    ret = _ret(name)
    current = r.get_or_none(__opts__, name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"Host {name} not found"
        return ret
    if r.is_in_maintenance(current) == bool(enabled):
        ret["comment"] = f"Host {name} is already {'in' if enabled else 'out of'} maintenance mode"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Host {name} would {'enter' if enabled else 'exit'} maintenance mode"
        return ret
    if enabled:
        r.enter_maintenance(__opts__, name, profile=profile)
    else:
        r.exit_maintenance(__opts__, name, profile=profile)
    ret["changes"] = {"maintenance": enabled}
    ret["comment"] = f"Host {name} {'entered' if enabled else 'exited'} maintenance mode"
    return ret
