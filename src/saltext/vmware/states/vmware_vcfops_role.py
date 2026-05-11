"""State module for VCF Operations RBAC roles (custom roles only).

System roles (Admin, ReadOnly, ...) cannot be deleted — ``absent`` will
no-op with a comment when targeted at a system-defined role.
"""

from saltext.vmware.clients import vcfops_auth as c

__virtualname__ = "vmware_vcfops_role"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, display_name=None, description="", privilege_keys=None, profile=None):
    ret = _ret(name)
    existing = c.roles_get_or_none(__opts__, name, profile=profile)
    if existing is not None:
        ret["comment"] = f"Role {name} already present"
        return ret
    spec = {
        "name": name,
        "displayName": display_name or name,
        "description": description,
        "privilege-keys": list(privilege_keys or []),
    }
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Role {name} would be created"
        return ret
    c.roles_create(__opts__, spec, profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Role {name} created"
    return ret


def absent(name, profile=None):
    ret = _ret(name)
    existing = c.roles_get_or_none(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"Role {name} already absent"
        return ret
    if existing.get("system-created") or existing.get("system-defined"):
        ret["comment"] = f"Role {name} is system-defined — refusing to delete"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Role {name} would be deleted"
        return ret
    c.roles_delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Role {name} deleted"
    return ret
