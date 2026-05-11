"""State module for Supervisor VM Classes."""

from saltext.vmware.clients import vcenter_vm_class as c

__virtualname__ = "vmware_vcenter_vm_class"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(
    name, cpu_count, memory_MB, profile=None, **spec
):  # noqa: N803  pylint: disable=invalid-name
    """Ensure VM class *name* exists with the given sizing.

    Extra keys in *spec* (``description``, ``cpu_reservation``,
    ``memory_reservation``, ``config_spec``) are forwarded as-is to the
    create call.
    """
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    desired = dict(spec)
    desired.update({"id": name, "cpu_count": cpu_count, "memory_MB": memory_MB})

    if existing is not None:
        drift = {
            k: (existing.get(k), v)
            for k, v in desired.items()
            if k not in ("id",) and existing.get(k) != v
        }
        if not drift:
            ret["comment"] = f"VM class {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"VM class {name} would be updated: {sorted(drift)}"
            return ret
        update_spec = {k: v for k, v in desired.items() if k != "id"}
        c.update(__opts__, name, update_spec, profile=profile)
        ret["changes"] = {"updated": sorted(drift)}
        ret["comment"] = f"VM class {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VM class {name} would be created"
        return ret
    c.create(__opts__, desired, profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"VM class {name} created"
    return ret


def absent(name, profile=None):
    ret = _ret(name)
    if c.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"VM class {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VM class {name} would be deleted"
        return ret
    c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"VM class {name} deleted"
    return ret
