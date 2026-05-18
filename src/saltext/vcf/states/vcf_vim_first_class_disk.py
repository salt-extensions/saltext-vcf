"""State module for First-Class Disks."""

from saltext.vcf.clients import vim_first_class_disk as c

__virtualname__ = "vcf_vim_first_class_disk"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_by_name(opts, datastore, name, profile=None):
    """Locate an FCD by display name on *datastore*. Returns the dict or None."""
    for fcd in c.list_(opts, datastore, profile=profile):
        if fcd["name"] == name:
            return fcd
    return None


def present(
    name,
    datastore,
    capacity_gb,
    provisioning="thin",
    keep_after_delete_vm=False,
    profile_id=None,
    profile=None,
):
    """Ensure an FCD named *name* with at least *capacity_gb* exists on *datastore*.

    If the disk exists but is smaller, it is grown (extend). Provisioning type
    is checked-only; it cannot be changed in-place.
    """
    ret = _ret(name)
    existing = _find_by_name(__opts__, datastore, name, profile=profile)
    desired_bytes = int(capacity_gb) * 1024 * 1024 * 1024
    if existing is not None:
        drift = {}
        if existing["capacity_bytes"] < desired_bytes:
            drift["capacity_bytes"] = (existing["capacity_bytes"], desired_bytes)
        if bool(existing["keep_after_delete_vm"]) != bool(keep_after_delete_vm):
            drift["keep_after_delete_vm"] = (
                existing["keep_after_delete_vm"],
                bool(keep_after_delete_vm),
            )
        if not drift:
            ret["comment"] = f"FCD {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"FCD {name} would change: {sorted(drift)}"
            return ret
        if "capacity_bytes" in drift:
            c.extend(__opts__, existing["id"], datastore, capacity_gb, profile=profile)
        if "keep_after_delete_vm" in drift:
            c.set_keep_after_delete_vm(
                __opts__, existing["id"], datastore, bool(keep_after_delete_vm), profile=profile
            )
        ret["changes"] = drift
        ret["comment"] = f"FCD {name} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"FCD {name} would be created on {datastore}"
        return ret
    task = c.create(
        __opts__,
        name,
        datastore,
        capacity_gb,
        provisioning=provisioning,
        profile_id=profile_id,
        keep_after_delete_vm=keep_after_delete_vm,
        profile=profile,
    )
    ret["changes"] = {"created_task": task}
    ret["comment"] = f"FCD {name} create task started"
    return ret


def absent(name, datastore, profile=None):
    """Ensure no FCD named *name* exists on *datastore*."""
    ret = _ret(name)
    existing = _find_by_name(__opts__, datastore, name, profile=profile)
    if existing is None:
        ret["comment"] = f"FCD {name} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"FCD {name} would be deleted"
        return ret
    c.delete(__opts__, existing["id"], datastore, profile=profile)
    ret["changes"] = {"deleted": existing["id"]}
    ret["comment"] = f"FCD {name} deleted"
    return ret
