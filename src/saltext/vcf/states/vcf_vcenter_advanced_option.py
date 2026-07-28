"""State module for vCenter Server advanced settings."""

from saltext.vcf.clients import vcenter_advanced_option as c

__virtualname__ = "vcf_vcenter_advanced_option"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def advanced_option(name, key=None, value=None, profile=None):
    """Ensure a vCenter Server advanced setting equals *value*.

    *name* is descriptive; *key* defaults to *name* when omitted. If the
    option has never been set before, it is created.
    """
    key = key or name
    ret = _ret(name)
    current = c.advanced_get(__opts__, key=key, profile=profile)

    if current == value:
        ret["comment"] = f"{key} already {value!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{key} would change from {current!r} to {value!r}"
        return ret
    c.advanced_set(__opts__, key, value, profile=profile)
    ret["changes"] = {"value": {"old": current, "new": value}}
    ret["comment"] = f"{key} updated to {value!r}"
    return ret
