"""NSX IP pools (/policy/api/v1/infra/ip-pools)."""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/ip-pools"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, pool_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{pool_id}", profile=profile)


def get_or_none(opts, pool_id, profile=None):
    try:
        return get(opts, pool_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, pool_id, profile=None, **spec):
    """Create or update an IP pool. *spec* is merged into the body."""
    body = {"display_name": spec.pop("display_name", pool_id)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{pool_id}", body=body, profile=profile)


def delete(opts, pool_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{pool_id}", profile=profile)


def list_subnets(opts, pool_id, profile=None):
    """List IP pool subnets — the ranges that make up the pool."""
    return nsx.api_get(opts, f"{PATH}/{pool_id}/ip-subnets", profile=profile)


def create_subnet(opts, pool_id, subnet_id, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", subnet_id)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{pool_id}/ip-subnets/{subnet_id}", body=body, profile=profile)


def delete_subnet(opts, pool_id, subnet_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{pool_id}/ip-subnets/{subnet_id}", profile=profile)


def list_allocations(opts, pool_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{pool_id}/ip-allocations", profile=profile)
