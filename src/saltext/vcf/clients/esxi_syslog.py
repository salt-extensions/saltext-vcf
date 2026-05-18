"""ESXi syslog configuration."""

from saltext.vcf.utils import esxi

PATH = "/api/esx/syslog"


def get(opts, profile=None):
    """Return current syslog config (servers, log level, log dir, etc.)."""
    return esxi.api_get(opts, PATH, profile=profile)


def set_servers(opts, servers, profile=None):
    """Replace the remote syslog destination list.

    Each entry is a URL like ``udp://collector.example.com:514`` or
    ``tcp://collector.example.com:1514``.
    """
    return esxi.api_patch(opts, PATH, body={"servers": list(servers)}, profile=profile)


def set_log_level(opts, level, profile=None):
    """Set global syslog log level (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``)."""
    return esxi.api_patch(opts, PATH, body={"log_level": level}, profile=profile)
