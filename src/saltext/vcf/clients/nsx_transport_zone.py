"""NSX Management API — transport zones."""

import requests

from saltext.vcf.utils import nsx

PATH = "/api/v1/transport-zones"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, zone_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{zone_id}", profile=profile)


def get_or_none(opts, zone_id, profile=None):
    try:
        return get(opts, zone_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
