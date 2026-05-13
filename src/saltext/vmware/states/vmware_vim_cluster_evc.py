"""State module for cluster EVC mode."""

from saltext.vmware.clients import vim_cluster_evc as c

__virtualname__ = "vmware_vim_cluster_evc"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def mode(name, cluster=None, evc_mode_key=None, profile=None):
    """Ensure cluster EVC mode equals *evc_mode_key*, or disabled if None.

    *name* is informational; *cluster* defaults to *name*.
    """
    cluster = cluster or name
    ret = _ret(name)
    current = c.get(__opts__, cluster, profile=profile)
    desired = evc_mode_key
    cur_key = current.get("current_key") or None
    if cur_key == desired:
        ret["comment"] = f"EVC on {cluster} already {desired or 'disabled'}"
        return ret
    if desired is None:
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"EVC on {cluster} would be disabled"
            return ret
        c.disable(__opts__, cluster, profile=profile)
        ret["changes"] = {"evc": (cur_key, None)}
        ret["comment"] = f"EVC on {cluster} disabled"
        return ret
    supported = current.get("supported_keys") or []
    if supported and desired not in supported:
        ret["result"] = False
        ret["comment"] = f"EVC mode {desired!r} not supported on {cluster}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"EVC on {cluster} would change from {cur_key!r} to {desired!r}"
        return ret
    c.configure(__opts__, cluster, desired, profile=profile)
    ret["changes"] = {"evc": (cur_key, desired)}
    ret["comment"] = f"EVC on {cluster} set to {desired!r}"
    return ret
