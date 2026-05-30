"""State module for vCenter datacenters."""

from saltext.vcf.clients import vcenter_datacenter as r

__virtualname__ = "vcf_vcenter_datacenter"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, folder=None, profile=None):
    """Ensure a datacenter exists."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is not None:  # noqa: F821
        ret["comment"] = f"Datacenter {name} is already present"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"Datacenter {name} would be created"
        return ret
    created = r.create(__opts__, name, folder=folder, profile=profile)  # noqa: F821
    ret["changes"] = {"new": created.get("datacenter") or name}
    ret["comment"] = f"Datacenter {name} created"
    return ret


def absent(name, profile=None):
    """Ensure a datacenter is absent."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is None:  # noqa: F821
        ret["comment"] = f"Datacenter {name} is already absent"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"Datacenter {name} would be deleted"
        return ret
    r.delete(__opts__, name, profile=profile)  # noqa: F821
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Datacenter {name} deleted"
    return ret
