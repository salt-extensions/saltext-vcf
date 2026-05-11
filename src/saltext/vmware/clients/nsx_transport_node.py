"""NSX Management API — host transport nodes."""

import requests

from saltext.vmware.utils import nsx

PATH = "/api/v1/transport-nodes"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, node_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{node_id}", profile=profile)


def get_or_none(opts, node_id, profile=None):
    try:
        return get(opts, node_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
