"""State module for NSX Tier-1 gateway hardening (multicast disable)."""

from saltext.vcf.clients import nsx_tier1 as c

__virtualname__ = "vcf_nsx_tier1"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def multicast_enabled(name, enabled=True, locale_service="default", profile=None):
    """Ensure multicast on Tier-1 *name* matches ``enabled`` (idempotent)."""
    ret = _ret(name)
    current = c.multicast_get(__opts__, name, locale_service=locale_service, profile=profile)
    current_enabled = bool(current.get("enabled", False))
    desired = bool(enabled)
    if current_enabled == desired:
        ret["comment"] = f"Tier-1 {name} multicast already {'enabled' if desired else 'disabled'}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Tier-1 {name} multicast would be {'enabled' if desired else 'disabled'}"
        return ret
    c.multicast_set(__opts__, name, desired, locale_service=locale_service, profile=profile)
    ret["changes"] = {"enabled": {"old": current_enabled, "new": desired}}
    ret["comment"] = f"Tier-1 {name} multicast {'enabled' if desired else 'disabled'}"
    return ret


def multicast_disabled(name, locale_service="default", profile=None):
    """Ensure multicast on Tier-1 *name* is disabled."""
    return multicast_enabled(name, enabled=False, locale_service=locale_service, profile=profile)
