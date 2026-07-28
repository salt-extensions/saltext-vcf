"""State module for vCenter Server's AD domain join."""

from saltext.vcf.clients import vcenter_ad_domain as c

__virtualname__ = "vcf_vcenter_ad_domain"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def ad_joined(name, username=None, password=None, profile=None):
    """Ensure the vCenter Server is joined to AD domain *name*.

    *username*/*password* are only used to join; once joined, no further
    changes are made (rotate credentials via ``ad_absent`` + ``ad_joined``).
    """
    ret = _ret(name)
    existing = c.get(__opts__, name, profile=profile)
    if existing is not None:
        ret["comment"] = f"vCenter already joined to {name}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vCenter would join domain {name}"
        return ret
    provider_id = c.join(__opts__, name, username, password, profile=profile)
    ret["changes"] = {"new": provider_id}
    ret["comment"] = f"vCenter joined to {name}"
    return ret


def ad_absent(name, profile=None):
    """Ensure the vCenter Server is not joined to AD domain *name*."""
    ret = _ret(name)
    existing = c.get(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"vCenter is already not joined to {name}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vCenter would leave domain {name}"
        return ret
    c.leave(__opts__, existing["provider"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"vCenter left domain {name}"
    return ret
