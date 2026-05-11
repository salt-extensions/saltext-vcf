"""State module for Supervisor Services activation.

The catalog (registering content) is a one-shot install — handled by
:py:func:`installed`. Once installed, services have an activation state
(``ACTIVATED`` / ``DEACTIVATED``) we manage declaratively.
"""

from saltext.vmware.clients import vcenter_supervisor_service as c

__virtualname__ = "vmware_vcenter_supervisor_service"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def activated(name, profile=None):
    """Ensure Supervisor Service *name* is in the ACTIVATED state."""
    ret = _ret(name)
    svc = c.get_or_none(__opts__, name, profile=profile)
    if svc is None:
        ret["result"] = False
        ret["comment"] = f"Service {name} is not registered"
        return ret
    if svc.get("state") == "ACTIVATED":
        ret["comment"] = f"Service {name} is already activated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be activated"
        return ret
    c.activate(__opts__, name, profile=profile)
    ret["changes"] = {"state": ("DEACTIVATED", "ACTIVATED")}
    ret["comment"] = f"Service {name} activated"
    return ret


def deactivated(name, profile=None):
    ret = _ret(name)
    svc = c.get_or_none(__opts__, name, profile=profile)
    if svc is None:
        ret["result"] = False
        ret["comment"] = f"Service {name} is not registered"
        return ret
    if svc.get("state") == "DEACTIVATED":
        ret["comment"] = f"Service {name} is already deactivated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be deactivated"
        return ret
    c.deactivate(__opts__, name, profile=profile)
    ret["changes"] = {"state": ("ACTIVATED", "DEACTIVATED")}
    ret["comment"] = f"Service {name} deactivated"
    return ret


def absent(name, profile=None):
    ret = _ret(name)
    if c.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Service {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be removed"
        return ret
    c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Service {name} removed"
    return ret
