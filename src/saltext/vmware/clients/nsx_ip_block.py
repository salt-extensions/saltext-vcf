"""NSX IP blocks (/policy/api/v1/infra/ip-blocks)."""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/ip-blocks"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, block_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{block_id}", profile=profile)


def get_or_none(opts, block_id, profile=None):
    try:
        return get(opts, block_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, block_id, cidr, profile=None, **spec):
    """Create or update an IP block. *cidr* is the IPv4 CIDR."""
    body = {"display_name": spec.pop("display_name", block_id), "cidr": cidr}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{block_id}", body=body, profile=profile)


def delete(opts, block_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{block_id}", profile=profile)
