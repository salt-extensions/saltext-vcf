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
dereferenced.  On VCF 9.1 GA the situation is even simpler — the
``activeDirectoryAuthentication`` attribute is missing from
``configManager`` entirely until the host joins its first domain.  Both
surfaces are treated as "not joined" rather than failing the read.
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
    """Return the ``HostActiveDirectoryAuthentication`` managed object.

    On VCF 9.1 GA (and some other ESXi builds), hosts that have never been
    joined to an AD domain don't even expose the
    ``configManager.activeDirectoryAuthentication`` attribute — a direct
    ``getattr`` raises ``AttributeError``.  Callers must be prepared for
    ``None``.
    """
    return getattr(h.configManager, "activeDirectoryAuthentication", None)


def _ad_info(h):
    """Return ``HostActiveDirectoryInfo`` or ``None`` if never joined / unavailable.

    Several conditions can surface as "no AD info" on a healthy ESXi host:

    * VCF 9.1 GA hosts that have never been joined don't expose
      ``configManager.activeDirectoryAuthentication`` at all
      (``AttributeError``).
    * Some builds return HTTP 503 from the HostAuthenticationManager
      backing service the first time ``.info`` is dereferenced.
    * ``vim.fault.HostConfigFault`` / ``NotSupported`` may fire on
      non-AD-capable stacks.

    Treat all of those as "not joined".
    """
    mgr = _ad_mgr(h)
    if mgr is None:
        return None
    try:
        return mgr.info
    except (
        AttributeError,
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


def _require_ad_mgr(h):
    mgr = _ad_mgr(h)
    if mgr is None:
        raise RuntimeError(
            "Host does not expose configManager.activeDirectoryAuthentication; "
            "the ESXi build may not support native AD join."
        )
    return mgr


def join_domain(opts, host, domain_name, username, password, profile=None):
    """Join *host* to *domain_name* natively using AD credentials.

    Calls ``HostActiveDirectoryAuthentication.JoinDomain_Task`` with the
    supplied credentials.  Returns the task moId; callers that need to
    block should wrap in :func:`saltext.vcf.utils.vim.wait_for_task`.
    """
    h = _host(opts, host, profile=profile)
    task = _require_ad_mgr(h).JoinDomain_Task(
        domainName=domain_name, userName=username, password=password
    )
    return task._moId  # noqa: SLF001


def leave_domain(opts, host, force=False, profile=None):
    """Leave the current AD domain via ``LeaveCurrentDomain_Task``."""
    h = _host(opts, host, profile=profile)
    task = _require_ad_mgr(h).LeaveCurrentDomain_Task(force=bool(force))
    return task._moId  # noqa: SLF001
