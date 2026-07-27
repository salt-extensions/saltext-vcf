"""Idempotent state module for ESXi native Active Directory join.

Fulfils 912-controls ``ESXi.enable-ad-auth_adv``: join an ESXi host to an
AD domain directly (no auth proxy).  The CAM/auth-proxy variant lives in
``vcf_esxi_auth_proxy``.
"""

from saltext.vcf.clients import esxi_ad_auth as c

__virtualname__ = "vcf_esxi_ad_auth"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def joined(name, domain, username, password, host=None, profile=None):
    """Ensure *host* is AD-joined to *domain* using native credentials.

    No-op if the host is already joined to the same domain (case-insensitive
    compare).  If the host is joined to a *different* domain, refuses to
    switch — call :func:`left` first to move between domains intentionally.

    *name* is the target host (used verbatim as the pyVmomi HostSystem
    name or moId) unless *host* is passed explicitly.
    """
    target = host or name
    ret = _ret(name)
    current = c.get_ad_state(__opts__, target, profile=profile)
    if current.get("joined") and (current.get("domain") or "").lower() == domain.lower():
        ret["comment"] = f"already joined to {domain}"
        return ret
    if current.get("joined") and current.get("domain"):
        ret["result"] = False
        ret["comment"] = (
            f"joined to {current['domain']!r}, refusing to switch to {domain!r};"
            " use vcf_esxi_ad_auth.left first"
        )
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would join {domain}"
        return ret
    task_id = c.join_domain(__opts__, target, domain, username, password, profile=profile)
    ret["changes"] = {
        "joined": {"old": current.get("domain"), "new": domain},
        "task": task_id,
    }
    ret["comment"] = f"joined {domain}"
    return ret


def left(name, force=False, host=None, profile=None):
    """Ensure *host* is not joined to any AD domain."""
    target = host or name
    ret = _ret(name)
    current = c.get_ad_state(__opts__, target, profile=profile)
    if not current.get("joined"):
        ret["comment"] = "not joined to any AD domain"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would leave domain {current.get('domain')}"
        return ret
    task_id = c.leave_domain(__opts__, target, force=force, profile=profile)
    ret["changes"] = {
        "joined": {"old": current.get("domain"), "new": None},
        "task": task_id,
    }
    ret["comment"] = f"left domain {current.get('domain')}"
    return ret
