"""Client for the vCenter appliance NTP API under ``/api/appliance/ntp``."""

from saltext.vcf.utils import vcenter

_NTP = "/api/appliance/ntp"


def ntp_get(opts, profile=None):
    """Return the list of configured NTP servers."""
    return vcenter.api_get(opts, _NTP, profile=profile)


def ntp_set(opts, servers, profile=None):
    return vcenter.api_put(opts, _NTP, body={"servers": list(servers)}, profile=profile)
