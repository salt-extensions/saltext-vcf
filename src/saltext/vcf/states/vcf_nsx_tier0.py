"""State module for NSX Tier-0 gateway hardening (routing / multicast disable)."""

from saltext.vcf.clients import nsx_tier0 as c

__virtualname__ = "vcf_nsx_tier0"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _feature_enabled(name, feature, get_fn, set_fn, enabled, locale_service, profile):
    """Ensure *feature* on Tier-0 *name* matches ``enabled``. Idempotent PATCH."""
    ret = _ret(name)
    current = get_fn(__opts__, name, locale_service=locale_service, profile=profile)
    current_enabled = bool(current.get("enabled", False))
    desired = bool(enabled)
    if current_enabled == desired:
        ret["comment"] = f"Tier-0 {name} {feature} already {'enabled' if desired else 'disabled'}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Tier-0 {name} {feature} would be {'enabled' if desired else 'disabled'}"
        return ret
    set_fn(__opts__, name, desired, locale_service=locale_service, profile=profile)
    ret["changes"] = {"enabled": {"old": current_enabled, "new": desired}}
    ret["comment"] = f"Tier-0 {name} {feature} {'enabled' if desired else 'disabled'}"
    return ret


def bgp_enabled(name, enabled=True, locale_service="default", profile=None):
    """Ensure BGP on Tier-0 *name* matches ``enabled`` (idempotent)."""
    return _feature_enabled(name, "BGP", c.bgp_get, c.bgp_set, enabled, locale_service, profile)


def bgp_disabled(name, locale_service="default", profile=None):
    """Ensure BGP on Tier-0 *name* is disabled."""
    return bgp_enabled(name, enabled=False, locale_service=locale_service, profile=profile)


def ospf_enabled(name, enabled=True, locale_service="default", profile=None):
    """Ensure OSPF on Tier-0 *name* matches ``enabled`` (idempotent)."""
    return _feature_enabled(name, "OSPF", c.ospf_get, c.ospf_set, enabled, locale_service, profile)


def ospf_disabled(name, locale_service="default", profile=None):
    """Ensure OSPF on Tier-0 *name* is disabled."""
    return ospf_enabled(name, enabled=False, locale_service=locale_service, profile=profile)


def multicast_enabled(name, enabled=True, locale_service="default", profile=None):
    """Ensure multicast on Tier-0 *name* matches ``enabled`` (idempotent)."""
    return _feature_enabled(
        name, "multicast", c.multicast_get, c.multicast_set, enabled, locale_service, profile
    )


def multicast_disabled(name, locale_service="default", profile=None):
    """Ensure multicast on Tier-0 *name* is disabled."""
    return multicast_enabled(name, enabled=False, locale_service=locale_service, profile=profile)
