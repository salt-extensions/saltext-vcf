"""Client for the vCenter appliance BASH shell access API under ``/api/appliance/access/shell``."""

from saltext.vcf.utils import vcenter

_SHELL = "/api/appliance/access/shell"


def shell_get(opts, profile=None):
    """Return ``{"enabled": bool, "timeout": int}`` for BASH shell access."""
    return vcenter.api_get(opts, _SHELL, profile=profile)


def shell_set(opts, enabled, timeout=None, profile=None):
    body = {"enabled": bool(enabled)}
    if timeout is not None:
        body["timeout"] = timeout
    return vcenter.api_put(opts, _SHELL, body=body, profile=profile)
