"""Per-ESXi host config via SOAP (NTP, services, Active Directory, advanced settings).

Counterpart to the standalone-ESXi-only ``esxi_*`` clients: these target
hosts *managed by vCenter*, where the direct ``/api/`` surface is
locked. All operations route through pyVmomi managers on the
``HostSystem`` object.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for host in container.view:
            if host_id_or_name in (host._moId, host.name):  # noqa: SLF001
                return host
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


# ---------------------------------------------------------------------------
# NTP
# ---------------------------------------------------------------------------


def ntp_get(opts, host, profile=None):
    """Return ``{"servers": [...], "enabled": bool, "policy", "time_zone", "config_file"}``."""
    h = _host(opts, host, profile=profile)
    date_time_info = h.config.dateTimeInfo
    servers = list(date_time_info.ntpConfig.server or []) if date_time_info.ntpConfig else []
    services = h.config.service.service or []
    ntpd = next((s for s in services if s.key == "ntpd"), None)
    tz = getattr(date_time_info, "timeZone", None)
    ntp_file = getattr(date_time_info.ntpConfig, "configFile", None) if date_time_info.ntpConfig else None
    return {
        "servers": servers,
        "enabled": bool(ntpd.running) if ntpd else False,
        "policy": ntpd.policy if ntpd else "off",
        "time_zone": {
            "key": getattr(tz, "key", None),
            "name": getattr(tz, "name", None),
        }
        if tz is not None
        else None,
        "config_file": ntp_file,
    }


def ntp_set_servers(opts, host, servers, profile=None):
    """Replace the NTP server list."""
    h = _host(opts, host, profile=profile)
    cfg = vim.host.NtpConfig(server=list(servers))
    spec = vim.host.DateTimeConfig(ntpConfig=cfg)
    h.configManager.dateTimeSystem.UpdateDateTimeConfig(config=spec)


def ntp_set_running(opts, host, running, profile=None):
    """Start or stop the ``ntpd`` service."""
    h = _host(opts, host, profile=profile)
    svc = h.configManager.serviceSystem
    if running:
        svc.StartService(id="ntpd")
    else:
        svc.StopService(id="ntpd")


def ntp_set_policy(opts, host, policy, profile=None):
    """Set the service start policy. *policy* one of ``on`` | ``off`` | ``automatic``."""
    h = _host(opts, host, profile=profile)
    h.configManager.serviceSystem.UpdateServicePolicy(id="ntpd", policy=policy)


# ---------------------------------------------------------------------------
# Services (generic)
# ---------------------------------------------------------------------------


def service_list(opts, host, profile=None):
    """Return a list of ``{key, label, running, policy, required}`` per service."""
    h = _host(opts, host, profile=profile)
    out = []
    for svc in h.config.service.service or []:
        out.append(
            {
                "key": svc.key,
                "label": svc.label,
                "running": bool(svc.running),
                "policy": svc.policy,
                "required": bool(svc.required),
                "uninstallable": bool(svc.uninstallable),
            }
        )
    return out


def service_start(opts, host, service_id, profile=None):
    _host(opts, host, profile=profile).configManager.serviceSystem.StartService(id=service_id)


def service_stop(opts, host, service_id, profile=None):
    _host(opts, host, profile=profile).configManager.serviceSystem.StopService(id=service_id)


def service_restart(opts, host, service_id, profile=None):
    _host(opts, host, profile=profile).configManager.serviceSystem.RestartService(id=service_id)


def service_set_policy(opts, host, service_id, policy, profile=None):
    _host(opts, host, profile=profile).configManager.serviceSystem.UpdateServicePolicy(
        id=service_id, policy=policy
    )


# ---------------------------------------------------------------------------
# Active Directory
# ---------------------------------------------------------------------------


def ad_status(opts, host, profile=None):
    """Return AD join state ``{"joined": bool, "domain": str|None, "trust_status": ...}``."""
    h = _host(opts, host, profile=profile)
    auth_info = h.config.authenticationManagerInfo
    if not auth_info:
        return {"joined": False, "domain": None, "trust_status": None}
    for store in auth_info.authConfig or []:
        if isinstance(store, vim.host.ActiveDirectoryInfo):
            return {
                "joined": store.enabled,
                "domain": store.joinedDomain or None,
                "trust_status": str(store.trustedDomain) if store.trustedDomain else None,
            }
    return {"joined": False, "domain": None, "trust_status": None}


def ad_join(opts, host, domain, username, password, ou_path=None, profile=None):
    """Join the host to *domain* using the supplied creds. Returns task moId.

    *ou_path* is accepted for API symmetry but vCenter ignores it on the
    standard ``JoinDomain_Task`` call; use ``JoinDomainWithCAM_Task`` (not
    exposed here) for CAM-server-driven OU placement.
    """
    h = _host(opts, host, profile=profile)
    auth_mgr = h.configManager.authenticationManager
    task = auth_mgr.JoinDomain_Task(domainName=domain, userName=username, password=password)
    return task._moId  # noqa: SLF001


def ad_leave(opts, host, force=False, profile=None):
    """Leave the AD domain. Returns task moId."""
    h = _host(opts, host, profile=profile)
    task = h.configManager.authenticationManager.LeaveCurrentDomain_Task(force=bool(force))
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Advanced settings (HostAdvancedSystemInfo)
# ---------------------------------------------------------------------------


def advanced_get(opts, host, key=None, profile=None):
    """Return advanced settings.

    When *key* is provided, returns the single value (raises ``LookupError``
    if not found). Otherwise returns a ``{key: value}`` dict.
    """
    h = _host(opts, host, profile=profile)
    settings = (
        h.configManager.advancedOption.QueryOptions(name=key)
        if key
        else h.configManager.advancedOption.setting
    )
    if key:
        if not settings:
            raise LookupError(f"advanced setting {key!r} not found")
        return settings[0].value
    return {s.key: s.value for s in (settings or [])}


def advanced_set(opts, host, key, value, profile=None):
    """Set a single advanced setting."""
    h = _host(opts, host, profile=profile)
    opt = vim.option.OptionValue(key=key, value=value)
    h.configManager.advancedOption.UpdateOptions(changedValue=[opt])


def advanced_set_many(opts, host, config_dict, profile=None):
    """Set multiple advanced settings in one call with type coercion.

    *config_dict* is ``{key: value}``; each value is type-cast using the
    host's declared ``supportedOption`` (``BoolOption`` / ``IntOption`` /
    ``LongOption``), mirroring ``vmware_esxi.set_advanced_configs``.
    """
    h = _host(opts, host, profile=profile)
    mgr = h.configManager.advancedOption
    supported = {}
    for opt in (getattr(mgr, "supportedOption", None) or []):
        try:
            supported[opt.key] = opt.optionType
        except AttributeError:
            continue
    changed = []
    for key, value in config_dict.items():
        option_type = supported.get(key)
        if option_type is not None:
            # pyvmomi instances type with the dotted class path
            # (``vim.option.BoolOption``), so use isinstance checks.
            if isinstance(option_type, vim.option.BoolOption):
                value = bool(value)
            elif isinstance(option_type, (vim.option.IntOption, vim.option.LongOption)):
                value = int(value)
            elif isinstance(option_type, vim.option.StringOption):
                value = str(value)
        changed.append(vim.option.OptionValue(key=key, value=value))
    mgr.UpdateOptions(changedValue=changed)
    return advanced_get(opts, host, profile=profile)


# ---------------------------------------------------------------------------
# Date/time (vmware_esxi.get_host_datetime parity)
# ---------------------------------------------------------------------------


def datetime_get(opts, host, profile=None):
    """Return the host's current date/time (ISO string) via ``HostDateTimeSystem``."""
    h = _host(opts, host, profile=profile)
    dt_mgr = h.configManager.dateTimeSystem
    if dt_mgr is None:
        raise RuntimeError(f"host {host!r} has no dateTimeSystem manager")
    dt = dt_mgr.QueryDateTime()
    return {"host": h.name, "datetime": dt.isoformat() if hasattr(dt, "isoformat") else str(dt)}
