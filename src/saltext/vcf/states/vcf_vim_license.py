"""State module for vSphere license management (``vmware_license_mgr`` parity)."""

from saltext.vcf.clients import vim_license as c

__virtualname__ = "vcf_vim_license"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(
    name,
    datacenter=None,
    cluster=None,
    esxi_hostname=None,
    profile=None,
):
    """Ensure license *name* is added to the pool and assigned.

    When no datacenter/cluster/esxi_hostname is given, the license is
    assigned to the vCenter itself.

    .. code-block:: yaml

        vSphere license:
          vcf_vim_license.present:
            - name: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    """
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    if existing is None:
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"license {name!r} would be added."
            ret["changes"] = {"new": name}
            return ret
        c.add(__opts__, name, profile=profile)
        ret["changes"] = {"new": name}
    assigned = [
        a
        for a in c.assigned_list(__opts__, profile=profile)
        if (a.get("assigned_license") or {}).get("license_key") == name
    ]
    entity_id = c.resolve_entity(
        __opts__, datacenter=datacenter, cluster=cluster, esxi_hostname=esxi_hostname, profile=profile
    )
    if any(a["entity_id"] == entity_id for a in assigned):
        ret["comment"] = ret["comment"] or f"license {name!r} already assigned."
        return ret
    if __opts__["test"] and not ret["changes"]:
        ret["result"] = None
        ret["comment"] = f"license {name!r} would be assigned."
        return ret
    c.assign_by_name(
        __opts__,
        name,
        datacenter=datacenter,
        cluster=cluster,
        esxi_hostname=esxi_hostname,
        profile=profile,
    )
    ret["changes"]["assigned_to"] = entity_id
    ret["comment"] = f"license {name!r} assigned."
    return ret


def absent(name, profile=None):
    """Ensure license *name* is removed from the license pool.

    .. code-block:: yaml

        Remove vSphere license:
          vcf_vim_license.absent:
            - name: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    """
    ret = _ret(name)
    if c.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"license {name!r} already absent."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"license {name!r} would be removed."
        ret["changes"] = {"old": name}
        return ret
    c.remove(__opts__, name, profile=profile)
    ret["changes"] = {"old": name}
    ret["comment"] = f"license {name!r} removed."
    return ret
