"""State module for ESXi advanced system settings."""

from saltext.vmware.clients import esxi_advanced as c

__virtualname__ = "vmware_esxi_advanced"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def setting(name, value, profile=None):
    """Ensure advanced setting *name* equals *value*."""
    ret = _ret(name)
    current = c.get_or_none(__opts__, name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"Advanced setting {name} does not exist on this host"
        return ret
    current_value = current.get("value")
    if current_value == value:
        ret["comment"] = f"{name} already {value!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{name} would change from {current_value!r} to {value!r}"
        return ret
    c.set_value(__opts__, name, value, profile=profile)
    ret["changes"] = {"value": {"old": current_value, "new": value}}
    ret["comment"] = f"{name} set to {value!r}"
    return ret
