"""State module for NSX Manager telemetry / CEIP opt-in.

Enforces the 912 Controls requirement that the NSX-T Manager must not send
environment information to third parties by pinning the CEIP
``ceip_acceptance`` flag to ``False`` (or an explicit caller-supplied value).
"""

from saltext.vcf.clients import nsx_telemetry as c

__virtualname__ = "vcf_nsx_telemetry"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def ceip_acceptance_set(name, ceip_acceptance=False, profile=None):
    """Ensure the NSX Manager CEIP ``ceip_acceptance`` flag matches *ceip_acceptance*.

    ``name`` is a label for the state and is not sent to NSX. The default of
    ``ceip_acceptance=False`` disables CEIP, satisfying the 912 Controls control.
    """
    ret = _ret(name)
    desired = bool(ceip_acceptance)
    current = c.get(__opts__, profile=profile) or {}
    current_val = bool(current.get("ceip_acceptance"))

    if current_val == desired:
        ret["comment"] = f"CEIP ceip_acceptance already {desired}"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"CEIP ceip_acceptance would change from {current_val} to {desired}"
        return ret

    c.set_ceip_acceptance(__opts__, desired, profile=profile)
    ret["changes"] = {"ceip_acceptance": {"old": current_val, "new": desired}}
    ret["comment"] = f"CEIP ceip_acceptance set to {desired}"
    return ret


def ceip_disabled(name, profile=None):
    """Convenience alias: ensure CEIP telemetry is opted out."""
    return ceip_acceptance_set(name, ceip_acceptance=False, profile=profile)
