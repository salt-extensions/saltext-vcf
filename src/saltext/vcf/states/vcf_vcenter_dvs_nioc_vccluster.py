"""State module for cluster-wide DVS Network I/O Control (NIOC)."""

from saltext.vcf.clients import vcenter_dvs_nioc_vccluster as c

__virtualname__ = "vcf_vcenter_dvs_nioc_vccluster"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def nioc_enabled(name, enabled, profile=None):
    """Ensure Network I/O Control is enabled/disabled on every DVS backing cluster *name*."""
    ret = _ret(name)
    desired = bool(enabled)
    current = c.nioc_get(__opts__, name, profile=profile)
    drift = {dvs: state for dvs, state in current.items() if state != desired}

    if not drift:
        ret["comment"] = f"NIOC on all DVS in cluster {name} already {desired}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"NIOC on {sorted(drift)} in cluster {name} would change to {desired}"
        return ret
    c.nioc_set(__opts__, name, desired, profile=profile)
    ret["changes"] = {dvs: {"old": state, "new": desired} for dvs, state in drift.items()}
    ret["comment"] = f"NIOC updated to {desired} on {sorted(drift)} in cluster {name}"
    return ret
