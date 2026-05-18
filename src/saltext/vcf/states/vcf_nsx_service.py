"""State module for NSX service definitions."""

from saltext.vcf.clients import nsx_service as c

__virtualname__ = "vcf_nsx_service"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, profile=None, **spec):
    ret = _ret(name)
    if c.get_or_none(__opts__, name, profile=profile) is not None:
        ret["comment"] = f"Service {name} is already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be created"
        return ret
    c.create(__opts__, name, profile=profile, **spec)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Service {name} created"
    return ret


def absent(name, profile=None):
    ret = _ret(name)
    if c.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Service {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be deleted"
        return ret
    c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Service {name} deleted"
    return ret
