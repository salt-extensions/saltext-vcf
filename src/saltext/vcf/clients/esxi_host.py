"""ESXi host system operations (info, lockdown, maintenance, power)."""

from saltext.vcf.utils import esxi

PATH = "/api/esx/host"


def info(opts, profile=None):
    """Return host system info (version, build, hardware summary)."""
    return esxi.api_get(opts, PATH, profile=profile)


def lockdown_get(opts, profile=None):
    """Return current lockdown mode config."""
    return esxi.api_get(opts, f"{PATH}/lockdown", profile=profile)


def lockdown_set(opts, mode, exception_users=None, profile=None):
    """Set lockdown mode. *mode* is one of ``NORMAL``, ``STRICT``, ``DISABLED``."""
    body = {"mode": mode}
    if exception_users is not None:
        body["exception_users"] = list(exception_users)
    return esxi.api_patch(opts, f"{PATH}/lockdown", body=body, profile=profile)


def enter_maintenance(opts, profile=None):
    return esxi.api_post(opts, f"{PATH}/maintenance", params={"action": "enter"}, profile=profile)


def exit_maintenance(opts, profile=None):
    return esxi.api_post(opts, f"{PATH}/maintenance", params={"action": "exit"}, profile=profile)


def reboot(opts, force=False, profile=None):
    return esxi.api_post(
        opts,
        f"{PATH}/power",
        body={"force": bool(force)},
        params={"action": "reboot"},
        profile=profile,
    )


def shutdown(opts, force=False, profile=None):
    return esxi.api_post(
        opts,
        f"{PATH}/power",
        body={"force": bool(force)},
        params={"action": "shutdown"},
        profile=profile,
    )


def is_in_maintenance(host_info):
    """True if *host_info* (from :func:`info`) reports maintenance mode."""
    return (
        bool(host_info.get("in_maintenance_mode"))
        or host_info.get("connection_state") == "MAINTENANCE"
    )
