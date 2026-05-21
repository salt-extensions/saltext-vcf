"""ESXi host system operations via SOAP/pyVmomi."""

from saltext.vcf.utils import esxi

# Maps SOAP lockdownMode enum values to the REST-style strings we expose.
_LOCKDOWN_FROM_SOAP = {
    "lockdownDisabled": "DISABLED",
    "lockdownNormal": "NORMAL",
    "lockdownStrict": "STRICT",
}
_LOCKDOWN_TO_SOAP = {v: k for k, v in _LOCKDOWN_FROM_SOAP.items()}


def info(opts, profile=None):
    """Return host system info (version, build, hardware summary)."""
    host = esxi.get_host_system(opts, profile=profile)
    summary = host.summary
    hw = host.hardware.systemInfo if host.hardware else None
    return {
        "version": summary.config.product.version,
        "build": summary.config.product.build,
        "product_name": summary.config.product.name,
        "vendor": hw.vendor if hw else None,
        "model": hw.model if hw else None,
        "in_maintenance_mode": summary.runtime.inMaintenanceMode,
        "connection_state": str(summary.runtime.connectionState),
        "power_state": str(summary.runtime.powerState),
    }


def lockdown_get(opts, profile=None):
    """Return current lockdown mode config."""
    host = esxi.get_host_system(opts, profile=profile)
    soap_mode = str(host.configManager.hostAccessManager.lockdownMode)
    return {"mode": _LOCKDOWN_FROM_SOAP.get(soap_mode, soap_mode)}


def lockdown_set(opts, mode, exception_users=None, profile=None):
    """Set lockdown mode. *mode* is one of ``NORMAL``, ``STRICT``, ``DISABLED``."""
    host = esxi.get_host_system(opts, profile=profile)
    mgr = host.configManager.hostAccessManager
    soap_mode = _LOCKDOWN_TO_SOAP.get(mode, mode)
    mgr.ChangeLockdownMode(mode=soap_mode)
    if exception_users is not None:
        mgr.UpdateLockdownExceptions(users=list(exception_users))
    return lockdown_get(opts, profile=profile)


def enter_maintenance(opts, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.EnterMaintenanceMode_Task(timeout=0)
    return {"status": "entering maintenance"}


def exit_maintenance(opts, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.ExitMaintenanceMode_Task(timeout=0)
    return {"status": "exiting maintenance"}


def reboot(opts, force=False, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.RebootHost_Task(force=bool(force))
    return {"status": "rebooting"}


def shutdown(opts, force=False, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.ShutdownHost_Task(force=bool(force))
    return {"status": "shutting down"}


def is_in_maintenance(host_info):
    """True if *host_info* (from :func:`info`) reports maintenance mode."""
    return (
        bool(host_info.get("in_maintenance_mode"))
        or host_info.get("connection_state") == "MAINTENANCE"
    )
