"""State module for a vCenter cluster's root resource pool share-level config."""

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


def shares(name, cpu=None, memory=None, profile=None):
    """Ensure CPU and/or memory allocation on cluster *name*'s root resource pool
    match the desired spec.

    *cpu* and *memory* are dicts with keys ``reservation``,
    ``expandable_reservation``, ``limit``, ``shares_level``, ``shares_value``.
    """
    ret = _ret(name)
    current = c.get_shares(__opts__, name, profile=profile)
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
        ret["comment"] = f"{name} root resource pool already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{name} root resource pool shares would change: {sorted(drift)}"
        return ret
    c.set_shares(__opts__, name, cpu=cpu, memory=memory, profile=profile)
    ret["changes"] = drift
    ret["comment"] = f"{name} root resource pool shares updated"
    return ret
