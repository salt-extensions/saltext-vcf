"""State module for vSAN fault-domain assignments."""

from saltext.vcf.clients import vsan_fault_domain as c

__virtualname__ = "vcf_vsan_fault_domain"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def member(name, mapping, profile=None):
    """Ensure cluster *name* has the given host→fault-domain *mapping*.

    *mapping* is ``{host_name_or_id: fault_domain_name}``. Hosts not in
    the mapping are left unchanged.
    """
    ret = _ret(name)
    current = c.list_(__opts__, name, profile=profile)
    current_by_host = {entry["host"]: entry.get("fault_domain") for entry in current}
    current_by_id = {entry["host_id"]: entry.get("fault_domain") for entry in current}

    drift = {}
    for host_key, desired in mapping.items():
        actual = current_by_host.get(host_key) or current_by_id.get(host_key)
        if actual != desired:
            drift[host_key] = {"old": actual, "new": desired}

    if not drift:
        ret["comment"] = f"Cluster {name} fault domains already match"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Cluster {name} fault domains would change: {sorted(drift)}"
        return ret

    task_id = c.assign(__opts__, name, mapping, profile=profile)
    ret["changes"] = {**drift, "task_id": task_id}
    ret["comment"] = f"Cluster {name} fault domain reassignment submitted (task={task_id})"
    return ret
