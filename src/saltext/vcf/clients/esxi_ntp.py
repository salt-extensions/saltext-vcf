"""ESXi NTP configuration."""

from saltext.vcf.utils import esxi

PATH = "/api/esx/ntp"


def get(opts, profile=None):
    """Return ``{"servers": [...], "enabled": bool}``."""
    return esxi.api_get(opts, PATH, profile=profile)


def set_servers(opts, servers, profile=None):
    """Replace the NTP server list."""
    return esxi.api_patch(opts, PATH, body={"servers": list(servers)}, profile=profile)


def set_enabled(opts, enabled, profile=None):
    return esxi.api_patch(opts, PATH, body={"enabled": bool(enabled)}, profile=profile)
