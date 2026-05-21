"""ESXi syslog configuration via SOAP/pyVmomi.

ESXi syslog is configured through advanced settings. The relevant keys:

- ``Syslog.global.logHost``   — comma-separated remote syslog destinations
  (e.g. ``udp://collector.example.com:514``).
- ``Syslog.global.logLevel``  — ``debug``, ``info``, ``warning``, ``error``.

ESXi stores logHost as a comma-separated string; we present it as a list
to match the REST surface.
"""

from pyVmomi import vim
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from saltext.vcf.utils import esxi

_KEY_LOG_HOST = "Syslog.global.logHost"
_KEY_LOG_LEVEL = "Syslog.global.logLevel"


def _adv_get(adv_mgr, key, default=""):
    try:
        opts = adv_mgr.QueryOptions(name=key)
        return opts[0].value if opts else default
    except (vim.fault.VimFault, vmodl.MethodFault):
        return default


def get(opts, profile=None):
    """Return current syslog config (servers, log level)."""
    host = esxi.get_host_system(opts, profile=profile)
    adv = host.configManager.advancedOption

    raw_hosts = _adv_get(adv, _KEY_LOG_HOST, "")
    log_level = _adv_get(adv, _KEY_LOG_LEVEL, "info")

    servers = [s.strip() for s in raw_hosts.split(",") if s.strip()] if raw_hosts else []
    return {
        "servers": servers,
        "log_level": log_level.upper(),
    }


def set_servers(opts, servers, profile=None):
    """Replace the remote syslog destination list.

    Each entry is a URL like ``udp://collector.example.com:514`` or
    ``tcp://collector.example.com:1514``.
    """
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.advancedOption.UpdateValues(
        changedValue=[vim.option.OptionValue(key=_KEY_LOG_HOST, value=",".join(servers))]
    )
    return get(opts, profile=profile)


def set_log_level(opts, level, profile=None):
    """Set global syslog log level (``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``)."""
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.advancedOption.UpdateValues(
        changedValue=[vim.option.OptionValue(key=_KEY_LOG_LEVEL, value=level.lower())]
    )
    return get(opts, profile=profile)
