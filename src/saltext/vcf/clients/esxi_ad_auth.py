"""ESXi native Active Directory join via SOAP/pyVmomi.

Covers the 912-controls requirement ``ESXi.enable-ad-auth_adv``: allow ESXi
hosts to join an Active Directory domain natively — i.e. sending the AD
credentials directly to the host rather than going through the vSphere
Authentication Proxy (CAM).  The CAM path is a separate control and is
shipped as ``vcf_esxi_auth_proxy`` (``ESXi.enable-auth-proxy``).

The join is done through the host's
``configManager.activeDirectoryAuthentication`` managed object:

* ``.info`` -> ``HostActiveDirectoryInfo`` with ``joinedDomain``,
  ``trustedDomain``, ``domainMembershipStatus`` and ``smbFileShares``.
* ``.JoinDomain_Task(domainName, userName, password)`` — direct join with
  plaintext AD credentials.
* ``.LeaveCurrentDomain_Task(force=True/False)`` — leave.

On hosts that have never been joined some ESXi builds surface a 503 from
the HostAuthenticationManager backing service when ``.info`` is
dereferenced; treat that as "not joined" rather than failing the read.
"""

import http.client
import logging

from pyVmomi import vim
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from saltext.vcf.utils import vim as soap

log = logging.getLogger(__name__)


def _host(opts, host, profile=None):
    return soap.resolve_host_system(opts, host, profile=profile)


def _ad_mgr(h):
    """Return the ``HostActiveDirectoryAuthentication`` managed object."""
    return h.configManager.activeDirectoryAuthentication


def _ad_info(h):
    """Return ``HostActiveDirectoryInfo`` or ``None`` if never joined / unavailable.

    ESXi builds that have never joined an AD domain sometimes return a 503
    from the HostAuthenticationManager backing service the first time
    ``.info`` is dereferenced.  A ``vim.fault.HostConfigFault`` /
    ``NotSupported`` may also fire on non-AD-capable stacks.  Treat all of
    those as "not joined".
    """
    try:
        return _ad_mgr(h).info
    except (
        http.client.HTTPException,
        vim.fault.VimFault,
        vmodl.MethodFault,
        ConnectionError,
    ) as exc:  # pragma: no cover - runtime shape varies
        log.debug("activeDirectoryAuthentication.info unavailable: %s", exc)
        return None


def get_ad_state(opts, host, profile=None):
    """Return the AD-join state for *host*.

    ::

        {
            "joined": bool,
            "domain": str | None,
            "trusted_domains": list[str],
            "membership_status": str | None,
            "smb_file_shares": str | None,
        }

    Never raises for the "never-joined" case — returns
    ``{"joined": False, "domain": None, ...}``.
    """
    h = _host(opts, host, profile=profile)
    info = _ad_info(h)
    if info is None:
        return {
            "joined": False,
            "domain": None,
            "trusted_domains": [],
            "membership_status": None,
            "smb_file_shares": None,
        }
    joined_domain = getattr(info, "joinedDomain", None) or None
    return {
        "joined": bool(joined_domain),
        "domain": joined_domain,
        "trusted_domains": list(getattr(info, "trustedDomain", None) or []),
        "membership_status": getattr(info, "domainMembershipStatus", None) or None,
        "smb_file_shares": getattr(info, "smbFileShares", None),
    }


def join_domain(opts, host, domain_name, username, password, profile=None):
    """Join *host* to *domain_name* natively using AD credentials.

    Calls ``HostActiveDirectoryAuthentication.JoinDomain_Task`` with the
    supplied credentials.  Returns the task moId; callers that need to
    block should wrap in :func:`saltext.vcf.utils.vim.wait_for_task`.
    """
    h = _host(opts, host, profile=profile)
    task = _ad_mgr(h).JoinDomain_Task(domainName=domain_name, userName=username, password=password)
    return task._moId  # noqa: SLF001


def leave_domain(opts, host, force=False, profile=None):
    """Leave the current AD domain via ``LeaveCurrentDomain_Task``."""
    h = _host(opts, host, profile=profile)
    task = _ad_mgr(h).LeaveCurrentDomain_Task(force=bool(force))
    return task._moId  # noqa: SLF001
