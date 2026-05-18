"""State module for NSX segments."""

from saltext.vcf.clients import nsx_segment as r

__virtualname__ = "vcf_nsx_segment"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, profile=None, **spec):
    """Ensure an NSX segment exists. *spec* is merged into the PUT body."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is not None:
        ret["comment"] = f"Segment {name} is already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Segment {name} would be created"
        return ret
    r.create(__opts__, name, profile=profile, **spec)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Segment {name} created"
    return ret


def absent(name, profile=None):
    """Ensure an NSX segment is removed."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Segment {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Segment {name} would be deleted"
        return ret
    r.delete(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Segment {name} deleted"
    return ret
