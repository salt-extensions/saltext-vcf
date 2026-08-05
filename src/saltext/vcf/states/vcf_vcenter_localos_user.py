"""State module for vCenter Server Appliance (VAMI) local OS user accounts."""

from saltext.vcf.clients import vcenter_localos_user as c

__virtualname__ = "vcf_vcenter_localos_user"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, password, roles, email=None, full_name=None, enabled=True, profile=None):
    """Ensure local OS account *name* exists with the given roles/contact info.

    Password rotation is intentionally not reconciled here: the VAMI API can
    only change a password given the current *old* password, and forcing a
    change without it means deleting and recreating the account -- which
    destroys its home directory. Set the password at creation; rotate it
    out-of-band (or via ``vcf_vcenter_localos_user.update`` with an explicit
    ``old_password``) when needed.
    """
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)

    if existing is None:
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"local OS account {name} would be created"
            return ret
        extra = {"enabled": enabled}
        if email is not None:
            extra["email"] = email
        if full_name is not None:
            extra["full_name"] = full_name
        c.create(__opts__, name, password, roles, profile=profile, **extra)
        ret["changes"] = {"new": name}
        ret["comment"] = f"local OS account {name} created"
        return ret

    wanted = {"roles": list(roles), "enabled": enabled}
    if email is not None:
        wanted["email"] = email
    diff = {k: v for k, v in wanted.items() if existing.get(k) != v}
    if full_name is not None and existing.get("fullname") != full_name:
        diff["full_name"] = full_name

    if not diff:
        ret["comment"] = f"local OS account {name} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"local OS account {name} would change: {diff}"
        return ret
    c.update(__opts__, name, profile=profile, **diff)
    ret["changes"] = diff
    ret["comment"] = f"local OS account {name} updated"
    return ret


def absent(name, profile=None):
    """Ensure no local OS account named *name* exists."""
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"local OS account {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"local OS account {name} would be deleted"
        return ret
    c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"local OS account {name} deleted"
    return ret
