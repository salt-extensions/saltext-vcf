"""Ensure a local vCenter SSO group exists using appliance SSH/dir-cli."""

from saltext.vcf.clients import vcenter_sso_group as c

__virtualname__ = "vcf_vcenter_sso_group"


def __virtual__():
    return __virtualname__


def present(name, domain, description="", profile=None):
    """Presence only: existing groups, descriptions and memberships are preserved."""
    ret = {"name": name, "result": True, "changes": {}, "comment": ""}
    try:
        existing = c.get_or_none(__opts__, name, domain, profile=profile)
        if existing is not None:
            ret["comment"] = f"SSO group {name}@{domain} already exists"
        elif __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"SSO group {name}@{domain} would be created"
        else:
            created = c.create(__opts__, name, domain, description=description, profile=profile)
            ret["changes"] = {"new": created}
            ret["comment"] = f"SSO group {name}@{domain} created and verified"
    except (ValueError, RuntimeError) as exc:
        ret["result"] = False
        ret["comment"] = str(exc)
    return ret
