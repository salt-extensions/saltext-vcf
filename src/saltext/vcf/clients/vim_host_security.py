"""Per-ESXi security and storage config via SOAP.

Companion to :mod:`vim_host_config` (NTP/AD/services/advanced). This
module covers:

* Lockdown mode (``HostAccessManager``)
* Local account CRUD (``HostLocalAccountManager``)
* iSCSI software initiator (``HostStorageSystem`` + iSCSI manager)
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for h in container.view:
            if host_id_or_name in (h._moId, h.name):  # noqa: SLF001
                return h
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


# ---------------------------------------------------------------------------
# Lockdown mode
# ---------------------------------------------------------------------------


def lockdown_get(opts, host, profile=None):
    """Return ``{"mode": "lockdownDisabled"|"lockdownNormal"|"lockdownStrict",
    "exception_users": [...]}``."""
    h = _host(opts, host, profile=profile)
    mode = str(h.config.adminDisabled and "lockdownNormal" or h.config.lockdownMode)
    if h.config.lockdownMode is not None:
        mode = str(h.config.lockdownMode)
    am = h.configManager.hostAccessManager
    if am is None:
        return {"mode": mode, "exception_users": []}
    users = (
        list(am.QueryLockdownExceptions() or []) if hasattr(am, "QueryLockdownExceptions") else []
    )
    return {"mode": mode, "exception_users": users}


def lockdown_set(opts, host, mode, profile=None):
    """Set lockdown *mode* (``lockdownDisabled`` | ``lockdownNormal`` |
    ``lockdownStrict``)."""
    h = _host(opts, host, profile=profile)
    h.configManager.hostAccessManager.ChangeLockdownMode(mode=mode)


def lockdown_set_exception_users(opts, host, users, profile=None):
    """Replace the exception-user list (users exempt from lockdown)."""
    h = _host(opts, host, profile=profile)
    h.configManager.hostAccessManager.UpdateLockdownExceptions(users=list(users))


# ---------------------------------------------------------------------------
# Local users (HostLocalAccountManager)
# ---------------------------------------------------------------------------


def user_list(opts, host, search_str="", exact=False, find_users=True, profile=None):
    """List local accounts matching *search_str* (empty = all).

    Uses ``UserDirectory.RetrieveUserGroups`` on the host's userDirectory.
    Returns a list of ``{principal, full_name, id, group, ...}`` dicts.
    """
    _host(opts, host, profile=profile)
    # The host's userDirectory exposes RetrieveUserGroups, but vCenter-managed
    # hosts route through their own content. We don't have direct access to
    # the host's content from here so fall back to the ServiceInstance content's
    # userDirectory which queries vCenter SSO.
    content = soap.content(opts, profile=profile)
    directory = content.userDirectory
    results = directory.RetrieveUserGroups(
        domain=None,
        searchStr=search_str,
        belongsToGroup=None,
        belongsToUser=None,
        exactMatch=bool(exact),
        findUsers=bool(find_users),
        findGroups=False,
    )
    out = []
    for u in results or []:
        out.append(
            {
                "principal": u.principal,
                "full_name": u.fullName,
                "group": bool(u.group),
            }
        )
    return out


def user_create(opts, host, username, password, description="", profile=None):
    """Create a local user on *host*. Returns nothing on success."""
    h = _host(opts, host, profile=profile)
    spec = vim.host.LocalAccountManager.AccountSpecification(
        id=username,
        password=password,
        description=description,
    )
    h.configManager.accountManager.CreateUser(user=spec)


def user_update(opts, host, username, password=None, description=None, profile=None):
    """Update a local user (password and/or description)."""
    h = _host(opts, host, profile=profile)
    spec = vim.host.LocalAccountManager.AccountSpecification(id=username)
    if password is not None:
        spec.password = password
    if description is not None:
        spec.description = description
    h.configManager.accountManager.UpdateUser(user=spec)


def user_delete(opts, host, username, profile=None):
    h = _host(opts, host, profile=profile)
    h.configManager.accountManager.RemoveUser(userName=username)


# ---------------------------------------------------------------------------
# iSCSI software initiator
# ---------------------------------------------------------------------------


def iscsi_status(opts, host, profile=None):
    """Return software iSCSI initiator status.

    Shape::

        {"enabled": bool, "hba_device": str|None, "iqn": str|None,
         "static_targets": [...], "send_targets": [...], "auth_type": "chap"|"none"}
    """
    h = _host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    hba = _iscsi_hba(storage)
    if hba is None:
        return {
            "enabled": False,
            "hba_device": None,
            "iqn": None,
            "static_targets": [],
            "send_targets": [],
            "auth_type": "none",
        }
    auth = hba.authenticationProperties
    return {
        "enabled": True,
        "hba_device": hba.device,
        "iqn": hba.iScsiName,
        "static_targets": [
            {"address": t.address, "port": t.port, "iqn": t.iScsiName}
            for t in (hba.configuredStaticTarget or [])
        ],
        "send_targets": [
            {"address": t.address, "port": t.port} for t in (hba.configuredSendTarget or [])
        ],
        "auth_type": "chap" if auth and auth.chapAuthEnabled else "none",
    }


def iscsi_enable(opts, host, profile=None):
    """Enable the software iSCSI initiator. Returns the HBA device name."""
    h = _host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    storage.UpdateSoftwareInternetScsiEnabled(enabled=True)
    storage.RescanAllHba()
    hba = _iscsi_hba(storage)
    return hba.device if hba else None


def iscsi_disable(opts, host, profile=None):
    h = _host(opts, host, profile=profile)
    h.configManager.storageSystem.UpdateSoftwareInternetScsiEnabled(enabled=False)


def iscsi_add_send_target(opts, host, address, port=3260, profile=None):
    """Add a Send Targets discovery address; the initiator will discover LUNs from it."""
    h = _host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    hba = _iscsi_hba(storage)
    if hba is None:
        raise LookupError("software iSCSI initiator not enabled")
    target = vim.host.InternetScsiHba.SendTarget(address=address, port=int(port))
    storage.AddInternetScsiSendTargets(iScsiHbaDevice=hba.device, targets=[target])
    storage.RescanHba(hbaDevice=hba.device)


def iscsi_remove_send_target(opts, host, address, port=3260, profile=None):
    h = _host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    hba = _iscsi_hba(storage)
    if hba is None:
        raise LookupError("software iSCSI initiator not enabled")
    target = vim.host.InternetScsiHba.SendTarget(address=address, port=int(port))
    storage.RemoveInternetScsiSendTargets(iScsiHbaDevice=hba.device, targets=[target])


def iscsi_set_chap(
    opts,
    host,
    *,
    name,
    password,
    direction="prohibited",
    profile=None,
):
    """Configure CHAP on the software iSCSI initiator.

    *direction* is one of ``required`` (mutual CHAP), ``preferred`` (mutual
    if peer supports), ``discouraged`` (per-target settings win), or
    ``prohibited`` (CHAP off).
    """
    h = _host(opts, host, profile=profile)
    storage = h.configManager.storageSystem
    hba = _iscsi_hba(storage)
    if hba is None:
        raise LookupError("software iSCSI initiator not enabled")
    auth_props = vim.host.InternetScsiHba.AuthenticationProperties(
        chapAuthEnabled=direction != "prohibited",
        chapName=name,
        chapSecret=password,
        chapAuthenticationType=f"chapAuthSetting.{direction}",
    )
    storage.UpdateInternetScsiAuthenticationProperties(
        iScsiHbaDevice=hba.device, authenticationProperties=auth_props
    )


def _iscsi_hba(storage_system):
    for hba in storage_system.storageDeviceInfo.hostBusAdapter or []:
        if isinstance(hba, vim.host.InternetScsiHba):
            return hba
    return None
