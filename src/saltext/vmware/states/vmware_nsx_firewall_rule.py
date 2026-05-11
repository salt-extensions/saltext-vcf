"""State module for NSX distributed firewall rules."""

from saltext.vmware.clients import nsx_firewall_rule as c

__virtualname__ = "vmware_nsx_firewall_rule"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, policy, domain="default", profile=None, **spec):
    """Ensure firewall rule *name* exists under *policy* in *domain*."""
    ret = _ret(name)
    if c.get_or_none(__opts__, name, policy, domain=domain, profile=profile) is not None:
        ret["comment"] = f"Rule {name} is already present in {policy}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Rule {name} would be created in {policy}"
        return ret
    c.create(__opts__, name, policy, domain=domain, profile=profile, **spec)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Rule {name} created in {policy}"
    return ret


def absent(name, policy, domain="default", profile=None):
    ret = _ret(name)
    if c.get_or_none(__opts__, name, policy, domain=domain, profile=profile) is None:
        ret["comment"] = f"Rule {name} is already absent from {policy}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Rule {name} would be deleted from {policy}"
        return ret
    c.delete(__opts__, name, policy, domain=domain, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Rule {name} deleted from {policy}"
    return ret
