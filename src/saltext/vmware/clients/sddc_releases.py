"""SDDC Manager release catalog (/v1/releases)."""

from saltext.vmware.utils import sddc

PATH = "/v1/releases"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def domain(opts, domain_id, profile=None):
    """Return release info for a specific workload domain."""
    return sddc.api_get(opts, PATH, params={"domainId": domain_id}, profile=profile)


def system(opts, profile=None):
    """Return the system-wide installed release info."""
    return sddc.api_get(opts, "/v1/system/release", profile=profile)
