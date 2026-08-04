"""State module for vCenter appliance BASH shell access configuration."""

from saltext.vcf.clients import vcenter_shell as c

__virtualname__ = "vcf_vcenter_shell"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def shell_access(name, enabled, timeout=None, profile=None):
    """Ensure BASH shell access matches *enabled* (and *timeout* minutes, if given).

    *name* is descriptive. Set *enabled* to ``False`` to disable the BASH
    shell (912 controls / STIG hardening).
    """
    ret = _ret(name)
    current = c.shell_get(__opts__, profile=profile) or {}
    desired_enabled = bool(enabled)

    actions = []
    changes = {}
    if bool(current.get("enabled")) != desired_enabled:
        actions.append(f"enabled={desired_enabled}")
        changes["enabled"] = {"old": current.get("enabled"), "new": desired_enabled}
    if timeout is not None and current.get("timeout") != timeout:
        actions.append(f"timeout={timeout}")
        changes["timeout"] = {"old": current.get("timeout"), "new": timeout}

    if not actions:
        ret["comment"] = "Shell access already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Shell access would change: {', '.join(actions)}"
        return ret
    c.shell_set(__opts__, desired_enabled, timeout=timeout, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"Shell access updated: {', '.join(actions)}"
    return ret
