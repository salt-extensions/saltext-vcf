"""State module for ESXi VIB acceptance level."""

from saltext.vmware.clients import vim_host_acceptance as c

__virtualname__ = "vmware_vim_host_acceptance"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def level(name, host=None, level=None, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure host acceptance level matches *level*."""
    host = host or name
    ret = _ret(name)
    if level is None:
        ret["result"] = False
        ret["comment"] = "level is required"
        return ret
    current = c.get(__opts__, host, profile=profile)
    if current == level:
        ret["comment"] = f"acceptance level on {host} already {level!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"acceptance level on {host} would change from {current!r} to {level!r}"
        return ret
    c.set_(__opts__, host, level, profile=profile)
    ret["changes"] = {"level": (current, level)}
    ret["comment"] = f"acceptance level on {host} set to {level!r}"
    return ret
