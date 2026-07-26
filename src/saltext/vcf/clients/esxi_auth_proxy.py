"""ESXi vSphere Authentication Proxy (CAM) configuration via SOAP/pyVmomi.

Covers the 912-controls requirement ``ESXi.enable-auth-proxy``: enable the
vSphere Authentication Proxy so ESXi hosts can join Active Directory without
AD credentials being sent from the client that runs the join.

The join itself is done through the host's
``configManager.authenticationManager.JoinDomainWithCAM_Task`` — that is the
pyVmomi call the auth proxy is designed to serve.  Two advanced settings
control the ESXi-side plumbing:

* ``UserVars.ActiveDirectoryVerifyCAMCertificate`` — 1 to require a valid
  CAM (Camellia) certificate, 0 to skip verification.
* ``Config.HostAgent.plugins.vmauthenticationservice.authproxyaddress`` —
  hostname/IP of the CAM appliance.

The advanced-setting keys are stable across ESXi 7.0/8.0/9.x; the
``JoinDomainWithCAM_Task`` shape is also stable (``domainName``,
``camServer``).  If a lab surfaces a divergence, prefer the shape ESXi
actually accepts and log an issue.
"""

from http.client import HTTPException

from pyVmomi import vim
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from saltext.vcf.utils import vim as soap

CAM_ADDRESS_KEY = "Config.HostAgent.plugins.vmauthenticationservice.authproxyaddress"
CAM_VERIFY_KEY = "UserVars.ActiveDirectoryVerifyCAMCertificate"


def _host(opts, host, profile=None):
    return soap.resolve_host_system(opts, host, profile=profile)


def _advanced_get(h, key):
    try:
        options = h.configManager.advancedOption.QueryOptions(name=key)
    except (vim.fault.VimFault, vmodl.MethodFault):
        return None
    if not options:
        return None
    return options[0].value


def _advanced_set(h, key, value):
    h.configManager.advancedOption.UpdateValues(
        changedValue=[vim.option.OptionValue(key=key, value=value)]
    )


def _ad_state(h):
    """Return ``{"joined": bool, "domain": str|None}`` from HostAuthenticationManager.

    Some ESXi builds (observed on VCF 9.1 GA) return an HTTP 503 from the
    HostAgent when the CAM/AD auth store info is queried through vCenter,
    presumably because the auth service is not initialized on a host that
    has never been joined to a domain.  Treat that surface as "unknown
    join state" — the advanced CAM settings we return alongside are still
    a truthful view of the ``ESXi.enable-auth-proxy`` config.
    """
    try:
        auth_mgr = h.configManager.authenticationManager
        info = getattr(auth_mgr, "info", None)
        stores = getattr(info, "authConfig", None) if info is not None else None
        if stores is None:
            # Some pyVmomi shapes surface authenticationManagerInfo on config.
            info = getattr(h.config, "authenticationManagerInfo", None) if h.config else None
            stores = getattr(info, "authConfig", None) if info is not None else None
        for store in stores or []:
            if isinstance(store, vim.host.ActiveDirectoryInfo):
                return {
                    "joined": bool(store.enabled),
                    "domain": store.joinedDomain or None,
                }
    except (HTTPException, vim.fault.VimFault, vmodl.MethodFault):
        return {"joined": False, "domain": None}
    return {"joined": False, "domain": None}


def get_config(opts, host, profile=None):
    """Return CAM configuration and current AD join state for *host*.

    ::

        {
            "cam_address": "cam.example.com" | None,
            "verify_cam_cert": True | False | None,
            "joined": bool,
            "domain": str | None,
        }
    """
    h = _host(opts, host, profile=profile)
    verify_raw = _advanced_get(h, CAM_VERIFY_KEY)
    verify_bool = None if verify_raw is None else bool(int(verify_raw))
    return {
        "cam_address": _advanced_get(h, CAM_ADDRESS_KEY) or None,
        "verify_cam_cert": verify_bool,
        **_ad_state(h),
    }


def set_config(opts, host, cam_address=None, verify_cam_cert=None, profile=None):
    """Set CAM advanced settings on *host*.

    Both fields are optional; passing ``None`` leaves that value alone.
    ``verify_cam_cert`` is coerced to the ``0``/``1`` int the setting stores.
    """
    h = _host(opts, host, profile=profile)
    if cam_address is not None:
        _advanced_set(h, CAM_ADDRESS_KEY, str(cam_address))
    if verify_cam_cert is not None:
        _advanced_set(h, CAM_VERIFY_KEY, 1 if verify_cam_cert else 0)
    return get_config(opts, host, profile=profile)


def join_domain_via_cam(opts, host, domain_name, cam_server, profile=None):
    """Join *host* to *domain_name* using the CAM (auth proxy) at *cam_server*.

    Calls ``HostActiveDirectoryAuthentication.JoinDomainWithCAM_Task``.
    Returns the task moId; callers that need to block should wrap in
    :func:`saltext.vcf.utils.vim.wait_for_task`.
    """
    h = _host(opts, host, profile=profile)
    task = h.configManager.authenticationManager.JoinDomainWithCAM_Task(
        domainName=domain_name, camServer=cam_server
    )
    return task._moId  # noqa: SLF001


def leave_domain(opts, host, force=False, profile=None):
    """Leave the current AD domain via ``LeaveCurrentDomain_Task``."""
    h = _host(opts, host, profile=profile)
    task = h.configManager.authenticationManager.LeaveCurrentDomain_Task(force=bool(force))
    return task._moId  # noqa: SLF001
