"""vCenter resource pool."""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/resource-pool"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, rp_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{rp_id}", profile=profile)


def get_or_none(opts, rp_id, profile=None):
    try:
        return get(opts, rp_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, name, parent, **spec):
    """Create a resource pool under *parent* resource pool id."""
    body = {"name": name, "parent": parent}
    body.update(spec)
    return vcenter.api_post(opts, PATH, body=body)


def delete(opts, rp_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{rp_id}", profile=profile)
