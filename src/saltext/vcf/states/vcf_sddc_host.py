"""State module for SDDC Manager host lifecycle."""

from saltext.vcf.clients import sddc_host as r

__virtualname__ = "vcf_sddc_host"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def commissioned(name, host_spec=None, profile=None):
    """Ensure a host is commissioned in SDDC Manager."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is not None:
        ret["comment"] = f"Host {name} is already commissioned"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Host {name} would be commissioned"
        return ret
    spec = host_spec or [{"hostfqdn": name}]
    r.commission(__opts__, spec, profile=profile)
    ret["changes"] = {"commissioned": name}
    ret["comment"] = f"Host {name} commissioned"
    return ret


def decommissioned(name, profile=None):
    """Ensure a host is decommissioned from SDDC Manager."""
    ret = _ret(name)
    if r.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Host {name} is already decommissioned"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Host {name} would be decommissioned"
        return ret
    r.decommission(__opts__, name, profile=profile)
    ret["changes"] = {"decommissioned": name}
    ret["comment"] = f"Host {name} decommissioned"
    return ret
