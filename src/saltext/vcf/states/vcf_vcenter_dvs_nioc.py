"""State module for DVS Network I/O Control (NIOC)."""

from saltext.vcf.clients import vcenter_dvs_nioc as c

__virtualname__ = "vcf_vcenter_dvs_nioc"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def nioc_enabled(name, enabled, profile=None):
    """Ensure Network I/O Control is enabled/disabled on DVS *name*."""
    ret = _ret(name)
    current = c.nioc_get(__opts__, name, profile=profile)
    desired = bool(enabled)

    if current == desired:
        ret["comment"] = f"NIOC on {name} already {desired}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"NIOC on {name} would change to {desired}"
        return ret
    c.nioc_set(__opts__, name, desired, profile=profile)
    ret["changes"] = {"enabled": {"old": current, "new": desired}}
    ret["comment"] = f"NIOC on {name} updated to {desired}"
    return ret
