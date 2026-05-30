"""State module for SDDC Manager workload domains."""

from saltext.vcf.clients import sddc_domain as r

__virtualname__ = "vcf_sddc_domain"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, spec, profile=None):
    """Ensure a workload domain exists by name."""
    ret = _ret(name)
    current = r.get_by_name(__opts__, name, profile=profile)  # noqa: F821
    if current is not None:
        ret["comment"] = f"Workload domain {name} is already present"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"Workload domain {name} would be created"
        return ret
    body = dict(spec)
    body.setdefault("domainName", name)
    created = r.create(__opts__, body, profile=profile)  # noqa: F821
    ret["changes"] = {"new": created.get("id") or name}
    ret["comment"] = f"Workload domain {name} created"
    return ret


def absent(name, profile=None):
    """Ensure a workload domain is marked for deletion."""
    ret = _ret(name)
    current = r.get_by_name(__opts__, name, profile=profile)  # noqa: F821
    if current is None:
        ret["comment"] = f"Workload domain {name} is already absent"
        return ret
    domain_id = current.get("id") or name
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"Workload domain {name} would be marked for deletion"
        return ret
    r.mark_for_deletion(__opts__, domain_id, profile=profile)  # noqa: F821
    ret["changes"] = {"marked_for_deletion": domain_id}
    ret["comment"] = f"Workload domain {name} marked for deletion"
    return ret
