"""State module for SDDC Manager-mediated VMSP services."""

from saltext.vmware.clients import sddc_vcf_services as c

__virtualname__ = "vmware_vcf_services"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def healthy(name, profile=None):
    """Assert that VMSP service *name* (e.g. ``COMMON_SERVICES``) is ``UP``.

    Read-only — never makes changes. Useful as a precondition state
    before fleet/SDDC LCM operations that depend on VMSP being healthy.
    """
    ret = _ret(name)
    svc = c.get_by_name(__opts__, name, profile=profile)
    if svc is None:
        ret["result"] = False
        ret["comment"] = f"VMSP service {name} not registered"
        return ret
    status = svc.get("status")
    if status != "UP":
        ret["result"] = False
        ret["comment"] = f"VMSP service {name} is {status!r}, expected UP"
        return ret
    ret["comment"] = f"VMSP service {name} is UP (version {svc.get('version')})"
    return ret
