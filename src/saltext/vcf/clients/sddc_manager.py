"""SDDC Manager node info (/v1/sddc-manager)."""

import requests

from saltext.vcf.utils import sddc


def get(opts, profile=None):
    """Return the SDDC Manager appliance info (singleton)."""
    return sddc.api_get(opts, "/v1/sddc-manager", profile=profile)


def get_or_none(opts, profile=None):
    try:
        return get(opts, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (404, 503):
            return None
        raise
