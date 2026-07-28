"""State module for vCenter custom attribute (custom field) definitions."""

from saltext.vcf.clients import vcenter_custom_attribute as c

__virtualname__ = "vcf_vcenter_custom_attribute"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, managed_object_type=None, profile=None):
    """Ensure a custom attribute definition named *name* exists."""
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    if existing is not None:
        ret["comment"] = f"custom attribute {name} already exists"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"custom attribute {name} would be created"
        return ret
    created = c.add(__opts__, name, managed_object_type=managed_object_type, profile=profile)
    ret["changes"] = {"new": created}
    ret["comment"] = f"custom attribute {name} created"
    return ret


def absent(name, profile=None):
    """Ensure no custom attribute definition named *name* exists."""
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"custom attribute {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"custom attribute {name} would be deleted"
        return ret
    c.remove(__opts__, existing["key"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"custom attribute {name} deleted"
    return ret
