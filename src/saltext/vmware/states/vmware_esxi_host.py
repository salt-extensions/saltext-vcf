"""State module for ESXi host system configuration."""

from saltext.vmware.clients import esxi_host as c

__virtualname__ = "vmware_esxi_host"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def maintenance(name, enabled=True, profile=None):
    """Ensure the ESXi host is in (or out of) maintenance mode.

    *name* is descriptive; the host targeted is whichever ESXi the pillar
    points at (or the current resource for resource framework calls).
    """
    ret = _ret(name)
    current = c.info(__opts__, profile=profile)
    in_maint = c.is_in_maintenance(current)
    if in_maint == bool(enabled):
        ret["comment"] = f"Host is already {'in' if enabled else 'out of'} maintenance mode"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Host would {'enter' if enabled else 'exit'} maintenance mode"
        return ret
    if enabled:
        c.enter_maintenance(__opts__, profile=profile)
    else:
        c.exit_maintenance(__opts__, profile=profile)
    ret["changes"] = {"maintenance": enabled}
    ret["comment"] = f"Host {'entered' if enabled else 'exited'} maintenance mode"
    return ret


def lockdown(name, mode="NORMAL", exception_users=None, profile=None):
    """Ensure lockdown mode matches *mode* (``NORMAL``, ``STRICT``, ``DISABLED``)."""
    ret = _ret(name)
    current = c.lockdown_get(__opts__, profile=profile) or {}
    current_mode = current.get("mode")
    current_excepts = sorted(current.get("exception_users") or [])
    desired_excepts = sorted(exception_users or [])
    if current_mode == mode and current_excepts == desired_excepts:
        ret["comment"] = f"Lockdown already at {mode}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Lockdown would change to {mode}"
        return ret
    c.lockdown_set(__opts__, mode, exception_users=exception_users, profile=profile)
    ret["changes"] = {"mode": {"old": current_mode, "new": mode}}
    if current_excepts != desired_excepts:
        ret["changes"]["exception_users"] = {
            "old": current_excepts,
            "new": desired_excepts,
        }
    ret["comment"] = f"Lockdown updated to {mode}"
    return ret
