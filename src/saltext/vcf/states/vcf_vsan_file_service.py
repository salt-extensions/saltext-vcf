"""State module for vSAN File Service."""

from saltext.vcf.clients import vsan_file_service as c

__virtualname__ = "vcf_vsan_file_service"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def configured(
    name,
    cluster,
    network_name,
    domain_name,
    ip_to_fqdn,
    subnet_mask,
    gateway_address,
    dns_suffixes,
    dns_address,
    ovf_url=None,
    profile=None,
):
    """Ensure vSAN File Service is enabled on *cluster* and *domain_name* exists.

    *name* is descriptive only. Mirrors the two-step nature of the
    underlying API: File Service must be enabled (which requires the FSVM
    OVF to have been downloaded first) before a domain can be created.
    Reconfigure/create calls are submitted async; this state doesn't block
    on task completion (same convention as ``vcf_vsan_cluster.configured``)
    -- poll ``vcf_vsan_file_service.list_domains`` separately if you need
    to confirm completion.
    """
    ret = _ret(name)
    changes = {}

    if not c.enabled(__opts__, cluster, profile=profile):
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"vSAN File Service would be enabled on {cluster}"
            return ret
        c.download_ovf(__opts__, cluster, ovf_url=ovf_url, profile=profile)
        task_id = c.set_enabled(__opts__, cluster, True, network_name=network_name, profile=profile)
        changes["enabled"] = {"old": False, "new": True, "task_id": task_id}

    if not c.domain_exists(__opts__, cluster, domain_name, profile=profile):
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"file service domain {domain_name} would be created on {cluster}"
            return ret
        task_id = c.create_domain(
            __opts__,
            cluster,
            domain_name,
            ip_to_fqdn,
            subnet_mask,
            gateway_address,
            dns_suffixes,
            dns_address,
            profile=profile,
        )
        changes["domain"] = {"old": None, "new": domain_name, "task_id": task_id}

    if not changes:
        ret["comment"] = f"vSAN File Service already configured on {cluster}"
        return ret
    ret["changes"] = changes
    ret["comment"] = f"vSAN File Service configuration submitted for {cluster}"
    return ret


def absent(name, cluster, domain_name=None, profile=None):
    """Ensure file service domain *domain_name* (if given) is removed, and
    vSAN File Service disabled on *cluster*.
    """
    ret = _ret(name)
    changes = {}

    if domain_name and c.domain_exists(__opts__, cluster, domain_name, profile=profile):
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"file service domain {domain_name} would be removed from {cluster}"
            return ret
        task_id = c.remove_domain(__opts__, cluster, domain_name, profile=profile)
        changes["domain"] = {"old": domain_name, "new": None, "task_id": task_id}

    if c.enabled(__opts__, cluster, profile=profile):
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"vSAN File Service would be disabled on {cluster}"
            return ret
        task_id = c.set_enabled(__opts__, cluster, False, profile=profile)
        changes["enabled"] = {"old": True, "new": False, "task_id": task_id}

    if not changes:
        ret["comment"] = f"vSAN File Service already absent on {cluster}"
        return ret
    ret["changes"] = changes
    ret["comment"] = f"vSAN File Service removal submitted for {cluster}"
    return ret
