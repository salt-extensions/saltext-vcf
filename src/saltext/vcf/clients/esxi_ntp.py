"""ESXi NTP configuration via SOAP/pyVmomi."""

from pyVmomi import vim

from saltext.vcf.utils import esxi


def get(opts, profile=None):
    """Return ``{"servers": [...], "enabled": bool}``."""
    host = esxi.get_host_system(opts, profile=profile)
    info = host.configManager.dateTimeSystem.QueryDateTimeInfo()

    ntpd_running = False
    for svc in host.configManager.serviceSystem.serviceInfo.service:
        if svc.key == "ntpd":
            ntpd_running = svc.running
            break

    return {
        "servers": list(info.ntpConfig.server or []),
        "enabled": ntpd_running,
    }


def set_servers(opts, servers, profile=None):
    """Replace the NTP server list."""
    host = esxi.get_host_system(opts, profile=profile)
    config = vim.host.DateTimeConfig(ntpConfig=vim.host.NtpConfig(server=list(servers)))
    host.configManager.dateTimeSystem.UpdateDateTimeConfig(config=config)
    return get(opts, profile=profile)


def set_enabled(opts, enabled, profile=None):
    svc_system = esxi.get_host_system(opts, profile=profile).configManager.serviceSystem
    if enabled:
        svc_system.Start(id="ntpd")
    else:
        svc_system.Stop(id="ntpd")
    return get(opts, profile=profile)
