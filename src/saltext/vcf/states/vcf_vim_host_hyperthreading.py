"""State module for ESXi hyperthreading."""

from saltext.vcf.clients import vim_host_hyperthreading as c

__virtualname__ = "vcf_vim_host_hyperthreading"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def enabled(name, host=None, enabled=True, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure hyperthreading config matches *enabled*. Reboot required to take effect."""
    host = host or name
    ret = _ret(name)
    current = c.get(__opts__, host, profile=profile)
    if not current["available"]:
        ret["result"] = False
        ret["comment"] = f"hyperthreading is not available on {host}"
        return ret
    if bool(current["config"]) == bool(enabled):
        ret["comment"] = f"hyperthreading on {host} already {'on' if enabled else 'off'}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"hyperthreading on {host} would be set to {bool(enabled)}"
        return ret
    if enabled:
        c.enable(__opts__, host, profile=profile)
    else:
        c.disable(__opts__, host, profile=profile)
    ret["changes"] = {"config": (current["config"], bool(enabled))}
    ret["comment"] = f"hyperthreading on {host} set to {bool(enabled)} (reboot required)"
    return ret
