"""State module for VCF Operations local users."""

from saltext.vmware.clients import vcfops_auth as c

__virtualname__ = "vmware_vcfops_user"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_by_username(username, profile=None):
    body = c.users_list(__opts__, profile=profile)
    users = body.get("users") if isinstance(body, dict) else None
    if not users:
        return None
    for user in users:
        if user.get("username") == username:
            return user
    return None


def present(
    name,
    password=None,
    first_name="",
    last_name="",
    email="",
    role_names=None,
    profile=None,
):
    """Ensure user *name* exists. Role assignment is by ``role_names`` list."""
    ret = _ret(name)
    existing = _find_by_username(name, profile=profile)
    spec = {
        "username": name,
        "firstName": first_name,
        "lastName": last_name,
        "emailAddress": email,
    }
    if password:
        spec["password"] = password
    if role_names is not None:
        spec["roleNames"] = list(role_names)
    if existing is not None:
        ret["comment"] = f"User {name} already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"User {name} would be created"
        return ret
    c.users_create(__opts__, spec, profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"User {name} created"
    return ret


def absent(name, profile=None):
    ret = _ret(name)
    existing = _find_by_username(name, profile=profile)
    if existing is None:
        ret["comment"] = f"User {name} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"User {name} would be deleted"
        return ret
    c.users_delete(__opts__, existing["id"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"User {name} deleted"
    return ret
