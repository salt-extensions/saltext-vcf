"""Idempotent state module for the ESXi vSphere Authentication Proxy (CAM).

Fulfils 912-controls ``ESXi.enable-auth-proxy`` — configure the auth proxy
address and (optionally) join AD through it so credentials never leave the
CAM appliance.
"""

from saltext.vcf.clients import esxi_auth_proxy as c

__virtualname__ = "vcf_esxi_auth_proxy"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def configured(name, cam_address, verify_cam_cert=True, host=None, profile=None):
    """Ensure the CAM advanced settings match.

    *name* is the target host (used verbatim as the pyVmomi HostSystem name
    or moId) unless *host* is passed explicitly.
    """
    target = host or name
    ret = _ret(name)
    current = c.get_config(__opts__, target, profile=profile)
    changes = {}
    if current.get("cam_address") != cam_address:
        changes["cam_address"] = {"old": current.get("cam_address"), "new": cam_address}
    desired_verify = bool(verify_cam_cert)
    if current.get("verify_cam_cert") is None or bool(current["verify_cam_cert"]) != desired_verify:
        changes["verify_cam_cert"] = {
            "old": current.get("verify_cam_cert"),
            "new": desired_verify,
        }
    if not changes:
        ret["comment"] = "CAM already configured"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"CAM would update: {', '.join(sorted(changes))}"
        return ret
    c.set_config(
        __opts__,
        target,
        cam_address=cam_address if "cam_address" in changes else None,
        verify_cam_cert=desired_verify if "verify_cam_cert" in changes else None,
        profile=profile,
    )
    ret["changes"] = changes
    ret["comment"] = f"CAM updated: {', '.join(sorted(changes))}"
    return ret


def joined(name, domain, cam_server, host=None, profile=None):
    """Ensure *host* is AD-joined to *domain* via the CAM at *cam_server*.

    No-op if the host is already joined to the same domain.  Different
    domain -> error (caller must first :func:`left` to move between domains
    intentionally).
    """
    target = host or name
    ret = _ret(name)
    current = c.get_config(__opts__, target, profile=profile)
    if current.get("joined") and (current.get("domain") or "").lower() == domain.lower():
        ret["comment"] = f"already joined to {domain}"
        return ret
    if current.get("joined") and current.get("domain"):
        ret["result"] = False
        ret["comment"] = (
            f"joined to {current['domain']!r}, refusing to switch to {domain!r};"
            " use vcf_esxi_auth_proxy.left first"
        )
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would join {domain} via CAM {cam_server}"
        return ret
    task_id = c.join_domain_via_cam(__opts__, target, domain, cam_server, profile=profile)
    ret["changes"] = {"joined": {"old": current.get("domain"), "new": domain}, "task": task_id}
    ret["comment"] = f"joined {domain} via CAM {cam_server}"
    return ret


def left(name, force=False, host=None, profile=None):
    """Ensure the host is not joined to any AD domain."""
    target = host or name
    ret = _ret(name)
    current = c.get_config(__opts__, target, profile=profile)
    if not current.get("joined"):
        ret["comment"] = "not joined to any AD domain"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would leave domain {current.get('domain')}"
        return ret
    task_id = c.leave_domain(__opts__, target, force=force, profile=profile)
    ret["changes"] = {"joined": {"old": current.get("domain"), "new": None}, "task": task_id}
    ret["comment"] = f"left domain {current.get('domain')}"
    return ret
