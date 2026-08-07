"""State module for named child resource pools under a vCenter cluster."""

from saltext.vcf.clients import vccluster_resource_pool as c

__virtualname__ = "vcf_vccluster_resource_pool"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _drift(current, desired):
    diff = {}
    for k, v in desired.items():
        if k not in current or current[k] != v:
            diff[k] = (current.get(k), v)
    return diff


def present(name, cluster, cpu=None, memory=None, profile=None):
    """Ensure resource pool *name* exists under *cluster*, with the given
    CPU/memory allocation.

    Creates the pool first if it doesn't exist yet (with vSphere's normal
    defaults), then reconciles *cpu*/*memory* — each a dict with any of
    ``reservation``, ``expandable_reservation``, ``limit``,
    ``shares_level``, ``shares_value``.
    """
    ret = _ret(name)
    created = False
    if c.get_or_none(__opts__, cluster, name, profile=profile) is None:
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"resource pool {name} would be created under {cluster}"
            return ret
        c.create(__opts__, cluster, name, profile=profile)
        created = True

    current = c.get_shares(__opts__, cluster, name, profile=profile)
    drift = {}
    if cpu is not None:
        d = _drift(current["cpu"], cpu)
        if d:
            drift["cpu"] = d
    if memory is not None:
        d = _drift(current["memory"], memory)
        if d:
            drift["memory"] = d

    if not drift:
        if created:
            ret["changes"] = {"new": name}
            ret["comment"] = f"resource pool {name} created under {cluster}"
        else:
            ret["comment"] = f"resource pool {name} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"resource pool {name} would change: {sorted(drift)}"
        return ret
    c.set_shares(__opts__, cluster, name, cpu=cpu, memory=memory, profile=profile)
    if created:
        drift["new"] = name
    ret["changes"] = drift
    ret["comment"] = f"resource pool {name} {'created and ' if created else ''}updated"
    return ret


def absent(name, cluster, profile=None):
    """Ensure no resource pool named *name* exists under *cluster*."""
    ret = _ret(name)
    if c.get_or_none(__opts__, cluster, name, profile=profile) is None:
        ret["comment"] = f"resource pool {name} is already absent under {cluster}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"resource pool {name} would be deleted from {cluster}"
        return ret
    c.delete(__opts__, cluster, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"resource pool {name} deleted from {cluster}"
    return ret
