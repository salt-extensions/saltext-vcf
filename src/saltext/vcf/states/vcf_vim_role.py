"""State module for vCenter authorization roles."""

from saltext.vcf.clients import vim_role as c

__virtualname__ = "vcf_vim_role"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, privileges, profile=None):
    """Ensure role *name* exists with the given privilege set.

    System-defined roles (``Admin``, ``ReadOnly``, ``View``, ``Anonymous``,
    ``NoAccess``) are immutable; the state refuses to modify them.
    """
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    desired = sorted(set(privileges))

    if existing is not None and existing.get("system"):
        ret["comment"] = f"Role {name} is system-defined; refusing to modify"
        return ret

    if existing is not None:
        current = sorted(set(existing.get("privilege", [])))
        if current == desired:
            ret["comment"] = f"Role {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            added = sorted(set(desired) - set(current))
            removed = sorted(set(current) - set(desired))
            ret["comment"] = f"Role {name} would be updated: +{added} -{removed}"
            return ret
        c.update(__opts__, name, desired, profile=profile)
        ret["changes"] = {
            "added": sorted(set(desired) - set(current)),
            "removed": sorted(set(current) - set(desired)),
        }
        ret["comment"] = f"Role {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Role {name} would be created"
        return ret
    c.create(__opts__, name, desired, profile=profile)
    ret["changes"] = {"new": name, "privileges": desired}
    ret["comment"] = f"Role {name} created"
    return ret


def absent(name, fail_if_used=True, profile=None):
    """Ensure role *name* does not exist."""
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"Role {name} is already absent"
        return ret
    if existing.get("system"):
        ret["comment"] = f"Role {name} is system-defined; refusing to delete"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Role {name} would be deleted"
        return ret
    c.delete(__opts__, name, fail_if_used=fail_if_used, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Role {name} deleted"
    return ret
