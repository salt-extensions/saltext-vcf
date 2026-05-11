"""State module for VCF Operations super metrics."""

from saltext.vmware.clients import vcfops_supermetric as c

__virtualname__ = "vmware_vcfops_supermetric"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_by_name(name):
    body = c.list_(__opts__)
    elements = body.get("superMetrics") if isinstance(body, dict) else None
    if not elements:
        return None
    for entry in elements:
        if entry.get("name") == name:
            return entry
    return None


def present(name, formula, description=""):
    ret = _ret(name)
    existing = _find_by_name(name)
    spec = {"name": name, "formula": formula, "description": description}
    if existing is not None:
        if existing.get("formula") == formula and existing.get("description", "") == description:
            ret["comment"] = f"Super metric {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Super metric {name} would be updated"
            return ret
        c.update(__opts__, existing["id"], spec)
        ret["changes"] = {"updated": name}
        ret["comment"] = f"Super metric {name} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Super metric {name} would be created"
        return ret
    c.create(__opts__, spec)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Super metric {name} created"
    return ret


def absent(name):
    ret = _ret(name)
    existing = _find_by_name(name)
    if existing is None:
        ret["comment"] = f"Super metric {name} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Super metric {name} would be deleted"
        return ret
    c.delete(__opts__, existing["id"])
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Super metric {name} deleted"
    return ret
