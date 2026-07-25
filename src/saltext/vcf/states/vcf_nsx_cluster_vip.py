"""State module for the NSX Manager cluster API VIP.

Wraps ``/api/v1/cluster/api-virtual-ip`` so an idempotent Salt state can
enforce the active/active cluster VIP required for management-plane HA
(912 Controls: "NSX-T Controller must be configured as a cluster in
active/active mode... configure NSX-T with a cluster VIP or external
load balancer").
"""

from saltext.vcf.clients import nsx_cluster as c

__virtualname__ = "vcf_nsx_cluster_vip"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _current_ip(opts, profile):
    resp = c.api_virtual_ip_get(opts, profile=profile) or {}
    # NSX returns the empty string when no VIP is configured.
    return resp.get("ip_address") or ""


def api_vip_set(name, ip_address=None, profile=None):
    """Ensure the cluster API VIP is set to *ip_address*.

    *name* may itself be the IP address; if ``ip_address`` is passed
    explicitly it wins so states can use a human-readable id in ``name``.

    No-op when the VIP already matches. When ``test=True``, only reports
    what would change.
    """
    target = ip_address or name
    ret = _ret(name)
    current = _current_ip(__opts__, profile)  # noqa: F821
    if current == target:
        ret["comment"] = f"NSX cluster API VIP is already {target}"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"NSX cluster API VIP would change from {current or '<unset>'} to {target}"
        ret["changes"] = {"old": current, "new": target}
        return ret
    c.api_virtual_ip_set(__opts__, target, profile=profile)  # noqa: F821
    ret["changes"] = {"old": current, "new": target}
    ret["comment"] = f"NSX cluster API VIP set to {target}"
    return ret


def api_vip_absent(name, profile=None):
    """Ensure the cluster API VIP is cleared.

    No-op when already unset.
    """
    ret = _ret(name)
    current = _current_ip(__opts__, profile)  # noqa: F821
    if not current:
        ret["comment"] = "NSX cluster API VIP is already cleared"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"NSX cluster API VIP would be cleared (was {current})"
        ret["changes"] = {"old": current, "new": ""}
        return ret
    c.api_virtual_ip_clear(__opts__, profile=profile)  # noqa: F821
    ret["changes"] = {"old": current, "new": ""}
    ret["comment"] = f"NSX cluster API VIP cleared (was {current})"
    return ret
