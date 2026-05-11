"""State module for vCenter object permissions."""

from saltext.vmware.clients import vim_permission as c

__virtualname__ = "vmware_vim_permission"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find(opts, entity_ref, principal, group, profile=None):
    for perm in c.list_(opts, entity_ref, inherited=False, profile=profile):
        if perm["principal"] == principal and bool(perm.get("group")) == bool(group):
            return perm
    return None


def present(name, entity_ref, principal, role, propagate=True, group=False, profile=None):
    """Ensure ``(principal, group)`` has *role* on *entity_ref* with *propagate*.

    The state ID *name* is informational; the identity tuple is
    ``(entity_ref, principal, group)``.
    """
    ret = _ret(name)
    existing = _find(__opts__, entity_ref, principal, group, profile=profile)
    if (
        existing is not None
        and existing["role"] == role
        and bool(existing["propagate"]) == bool(propagate)
    ):
        ret["comment"] = f"Permission for {principal} on {entity_ref} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Permission for {principal} on {entity_ref} would be set to {role}"
        return ret
    c.set_(__opts__, entity_ref, principal, role, propagate=propagate, group=group, profile=profile)
    if existing is None:
        ret["changes"] = {"new": {"principal": principal, "role": role, "propagate": propagate}}
        ret["comment"] = f"Permission for {principal} on {entity_ref} set to {role}"
    else:
        ret["changes"] = {
            "role": (existing["role"], role),
            "propagate": (existing["propagate"], propagate),
        }
        ret["comment"] = f"Permission for {principal} on {entity_ref} updated"
    return ret


def absent(name, entity_ref, principal, group=False, profile=None):
    """Ensure ``(principal, group)`` has no permission on *entity_ref*."""
    ret = _ret(name)
    existing = _find(__opts__, entity_ref, principal, group, profile=profile)
    if existing is None:
        ret["comment"] = f"Permission for {principal} on {entity_ref} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Permission for {principal} on {entity_ref} would be removed"
        return ret
    c.remove(__opts__, entity_ref, principal, group=group, profile=profile)
    ret["changes"] = {"removed": {"principal": principal, "role": existing["role"]}}
    ret["comment"] = f"Permission for {principal} on {entity_ref} removed"
    return ret
