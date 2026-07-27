"""State module for NSX Manager telemetry / CEIP opt-in.

Enforces the 912 Controls requirement that the NSX-T Manager must not send
environment information to third parties by pinning the CEIP ``optin`` flag
to ``False`` (or an explicit caller-supplied value).
"""

from saltext.vcf.clients import nsx_telemetry as c

__virtualname__ = "vcf_nsx_telemetry"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def optin_set(name, optin=False, profile=None):
    """Ensure the NSX Manager CEIP ``optin`` flag matches *optin*.

    ``name`` is a label for the state and is not sent to NSX. The default of
    ``optin=False`` disables CEIP, satisfying the 912 Controls control.
    """
    ret = _ret(name)
    desired = bool(optin)
    current = c.get(__opts__, profile=profile) or {}
    current_optin = bool(current.get("optin"))

    if current_optin == desired:
        ret["comment"] = f"CEIP optin already {desired}"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"CEIP optin would change from {current_optin} to {desired}"
        return ret

    c.set_optin(__opts__, desired, profile=profile)
    ret["changes"] = {"optin": {"old": current_optin, "new": desired}}
    ret["comment"] = f"CEIP optin set to {desired}"
    return ret


def ceip_disabled(name, profile=None):
    """Convenience alias: ensure CEIP telemetry is opted out."""
    return optin_set(name, optin=False, profile=profile)
