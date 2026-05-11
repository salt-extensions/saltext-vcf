"""State module for vCenter clusters."""

from saltext.vmware.clients import vcenter_cluster as r

__virtualname__ = "vmware_vcenter_cluster"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, profile=None, **kwargs):
    """Ensure a cluster with id *name* exists."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is not None:
        ret["comment"] = f"Cluster {name} is already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Cluster {name} would be created"
        return ret
    r.create(__opts__, name, profile=profile, **kwargs)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Cluster {name} created"
    return ret


def absent(name, profile=None):
    """Ensure a cluster with id *name* does not exist."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Cluster {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Cluster {name} would be deleted"
        return ret
    r.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Cluster {name} deleted"
    return ret
