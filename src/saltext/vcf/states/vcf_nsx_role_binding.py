"""State module for NSX RBAC role bindings.

Role bindings are looked up by *name* (e.g. an LDAP user/group). The state
matches against the `name` field returned by the list endpoint since the
``id`` is server-generated. For idempotency, *present* updates the existing
binding's roles when found by name, and creates a new one otherwise.
"""

from saltext.vcf.clients import nsx_role_binding as c

__virtualname__ = "vcf_nsx_role_binding"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_by_name(opts, name, profile=None):
    listed = c.list_(opts, profile=profile) or {}
    results = listed.get("results") or []
    for entry in results:
        if entry.get("name") == name:
            return entry
    return None


def present(name, type_, roles, profile=None, **spec):
    """Ensure a role binding for principal *name* exists with the given *roles*."""
    ret = _ret(name)
    current = _find_by_name(__opts__, name, profile=profile)
    desired_roles = sorted([r.get("role") for r in roles])

    if current is not None:
        current_roles = sorted([r.get("role") for r in current.get("roles", [])])
        if current_roles == desired_roles and current.get("type") == type_:
            ret["comment"] = f"Role binding {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Role binding {name} would be updated"
            return ret
        body = dict(current)
        body["roles"] = list(roles)
        body["type"] = type_
        c.update(__opts__, current["id"], body, profile=profile)
        ret["changes"] = {
            "roles": {"old": current_roles, "new": desired_roles},
        }
        ret["comment"] = f"Role binding {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Role binding {name} would be created"
        return ret
    c.create(__opts__, name, type_, roles, profile=profile, **spec)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Role binding {name} created"
    return ret


def absent(name, profile=None):
    ret = _ret(name)
    current = _find_by_name(__opts__, name, profile=profile)
    if current is None:
        ret["comment"] = f"Role binding {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Role binding {name} would be deleted"
        return ret
    c.delete(__opts__, current["id"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Role binding {name} deleted"
    return ret
