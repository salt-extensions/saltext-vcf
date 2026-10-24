"""State module for per-host vSAN configuration (SOAP)."""

from saltext.vcf.clients import vsan_disk as c

__virtualname__ = "vcf_vsan_disk"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def host_configured(name, host, enabled, profile=None):
    """Ensure vSAN is enabled (or disabled) on *host*.

    .. code-block:: yaml

        Host vSAN:
          vcf_vsan_disk.host_configured:
            - host: esxi-01
            - enabled: true
    """
    ret = _ret(name)
    current = c.host_config(__opts__, host, profile=profile)
    if bool(current.get("enabled")) == bool(enabled):
        ret["comment"] = f"vSAN on {host} already {'enabled' if enabled else 'disabled'}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vSAN on {host} would be {'enabled' if enabled else 'disabled'}."
        ret["changes"] = {"enabled": (current.get("enabled"), bool(enabled))}
        return ret
    c.host_enable(__opts__, host, enabled, profile=profile)
    ret["changes"] = {"enabled": (current.get("enabled"), bool(enabled))}
    ret["comment"] = f"vSAN on {host} {'enabled' if enabled else 'disabled'}."
    return ret
