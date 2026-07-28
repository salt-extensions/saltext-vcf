"""State module for vCenter appliance NTP configuration."""

from saltext.vcf.clients import vcenter_appliances as c

__virtualname__ = "vcf_vcenter_appliances"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def ntp_servers(name, servers, profile=None):
    """Ensure the appliance's NTP server list matches *servers*.

    *name* is descriptive.
    """
    ret = _ret(name)
    current_servers = sorted(c.ntp_get(__opts__, profile=profile) or [])
    desired_servers = sorted(servers)

    if current_servers == desired_servers:
        ret["comment"] = "NTP already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "NTP would change: servers"
        return ret
    c.ntp_set(__opts__, servers, profile=profile)
    ret["changes"] = {"servers": {"old": current_servers, "new": desired_servers}}
    ret["comment"] = "NTP updated: servers"
    return ret
