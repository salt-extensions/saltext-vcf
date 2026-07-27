"""State module for ESXi advanced system settings.

Also exposes named, discoverable wrappers for common 912 Controls
hardening items (``tps_disabled``) so a compliance SLS reads as a
control name rather than a pair of opaque ``Mem.*`` keys.
"""

from saltext.vcf.clients import esxi_advanced as c

__virtualname__ = "vcf_esxi_advanced"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def setting(name, value, profile=None):
    """Ensure advanced setting *name* equals *value*."""
    ret = _ret(name)
    current = c.get_or_none(__opts__, name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"Advanced setting {name} does not exist on this host"
        return ret
    current_value = current.get("value")
    if current_value == value:
        ret["comment"] = f"{name} already {value!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{name} would change from {current_value!r} to {value!r}"
        return ret
    c.set_value(__opts__, name, value, profile=profile)
    ret["changes"] = {"value": {"old": current_value, "new": value}}
    ret["comment"] = f"{name} set to {value!r}"
    return ret


# ---------------------------------------------------------------------------
# 912 Controls #30 -- Transparent Page Sharing (TPS) disable
# ---------------------------------------------------------------------------


TPS_DISABLE_SETTINGS = (
    ("Mem.ShareForceSalting", 2),
    ("Mem.ShareScanGHz", 0),
)


def tps_disabled(name, host=None, profile=None):
    """Ensure Transparent Page Sharing is disabled on the ESXi host.

    Sets ``Mem.ShareForceSalting = 2`` (per-VM salting -- no inter-VM
    sharing) and ``Mem.ShareScanGHz = 0`` (page-share scanner off) per
    912 Controls #30.

    *host* is accepted for SLS symmetry with the other 912-Controls
    hardening states -- the ESXi advanced-settings surface always
    targets the host pinned in the ``saltext.vcf.esxi`` pillar (or the
    profile override), so the argument is documentary only.
    """
    ret = _ret(name)
    changes = {}
    missing = []
    for key, desired in TPS_DISABLE_SETTINGS:
        current = c.get_or_none(__opts__, key, profile=profile)
        if current is None:
            missing.append(key)
            continue
        current_value = current.get("value")
        # ESXi returns numeric settings as ints; coerce for comparison.
        try:
            current_cmp = int(current_value)
        except (TypeError, ValueError):
            current_cmp = current_value
        if current_cmp == desired:
            continue
        changes[key] = {"old": current_value, "new": desired}

    if missing:
        ret["result"] = False
        ret["comment"] = f"Advanced setting(s) missing on this host: {missing}"
        return ret

    if not changes:
        ret["comment"] = "TPS already disabled (Mem.ShareForceSalting=2, Mem.ShareScanGHz=0)"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Would set {sorted(changes)} to disable TPS"
        ret["changes"] = changes
        return ret

    for key, spec in changes.items():
        c.set_value(__opts__, key, spec["new"], profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"Disabled TPS: set {sorted(changes)}"
    return ret
