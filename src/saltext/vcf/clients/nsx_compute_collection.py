"""NSX Management API — compute collections (vCenter clusters known to NSX)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/api/v1/fabric/compute-collections"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, collection_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{collection_id}", profile=profile)


def get_or_none(opts, collection_id, profile=None):
    try:
        return get(opts, collection_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
