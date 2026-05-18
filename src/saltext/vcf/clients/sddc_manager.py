"""SDDC Manager node info (/v1/sddc-manager)."""

from saltext.vcf.utils import sddc


def get(opts, profile=None):
    """Return the SDDC Manager appliance info (singleton)."""
    return sddc.api_get(opts, "/v1/sddc-manager", profile=profile)
