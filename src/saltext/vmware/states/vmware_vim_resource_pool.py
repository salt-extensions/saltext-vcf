"""State module for resource-pool share-level config (SOAP)."""

from saltext.vmware.clients import vim_resource_pool as c

__virtualname__ = "vmware_vim_resource_pool"


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


def shares(name, rp=None, cpu=None, memory=None, profile=None):
    """Ensure CPU and/or memory allocation match the desired spec.

    *rp* defaults to *name*. *cpu* and *memory* are dicts with keys
    ``reservation``, ``expandable_reservation``, ``limit``, ``shares_level``,
    ``shares_value``.
    """
    rp = rp or name
    ret = _ret(name)
    current = c.get_shares(__opts__, rp, profile=profile)
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
        ret["comment"] = f"{rp} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{rp} shares would change: {sorted(drift)}"
        return ret
    c.set_shares(__opts__, rp, cpu=cpu, memory=memory, profile=profile)
    ret["changes"] = drift
    ret["comment"] = f"{rp} shares updated"
    return ret
