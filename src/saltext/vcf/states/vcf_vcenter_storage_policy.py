"""State module for vCenter Storage Policy-Based Management (SPBM) policies."""

from saltext.vcf.clients import vcenter_storage_policy as c

__virtualname__ = "vcf_vcenter_storage_policy"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, constraints, description=None, profile=None):
    """Ensure a tag/capability-based storage policy named *name* exists with
    the given *constraints* (and *description*, if given).

    *constraints* is a list of rulesets: ``[{"tags": {"cat1": ["gold"]}},
    {"capabilities": {"VSAN.replicaPreference": "RAID-1 (Mirroring) - Performance"}}]``.
    Rulesets are OR-ed by the server; capabilities/tags within one ruleset
    are AND-ed.
    """
    ret = _ret(name)
    existing = c.get_by_name(__opts__, name, profile=profile)

    if existing is None:
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"storage policy {name} would be created"
            return ret
        policy_id = c.create(__opts__, name, constraints, description=description, profile=profile)
        ret["changes"] = {"new": policy_id}
        ret["comment"] = f"storage policy {name} created"
        return ret

    diff = {}
    if description is not None and existing.get("description") != description:
        diff["description"] = {"old": existing.get("description"), "new": description}
    if existing.get("constraints") != constraints:
        diff["constraints"] = {"old": existing.get("constraints"), "new": constraints}

    if not diff:
        ret["comment"] = f"storage policy {name} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"storage policy {name} would change: {sorted(diff)}"
        return ret
    c.update(__opts__, name, constraints=constraints, description=description, profile=profile)
    ret["changes"] = diff
    ret["comment"] = f"storage policy {name} updated"
    return ret


def default_policy(name, datastore, policy, profile=None):
    """Ensure *policy* (an existing named storage policy) is the default
    storage policy for *datastore*.

    *name* is descriptive only. *policy* must already exist (see
    :func:`present`) — this only assigns it, it doesn't create it.
    """
    ret = _ret(name)
    wanted = c.get_by_name(__opts__, policy, profile=profile)
    if wanted is None:
        ret["result"] = False
        ret["comment"] = f"storage policy {policy!r} does not exist"
        return ret

    current = c.default_policy_get(__opts__, datastore, profile=profile)
    if current == wanted["id"]:
        ret["comment"] = f"{datastore} default storage policy already {policy}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{datastore} default storage policy would change to {policy}"
        return ret
    c.default_policy_set(__opts__, datastore, policy, profile=profile)
    ret["changes"] = {"default_policy": {"old": current, "new": wanted["id"]}}
    ret["comment"] = f"{datastore} default storage policy set to {policy}"
    return ret


def absent(name, profile=None):
    """Ensure no storage policy named *name* exists."""
    ret = _ret(name)
    existing = c.get_by_name(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"storage policy {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"storage policy {name} would be deleted"
        return ret
    c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"storage policy {name} deleted"
    return ret
