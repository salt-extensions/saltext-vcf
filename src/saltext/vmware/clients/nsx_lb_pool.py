"""NSX Load Balancer pool (Policy API /infra/lb-pools)."""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/lb-pools"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, pool, profile=None):
    return nsx.api_get(opts, f"{PATH}/{pool}", profile=profile)


def get_or_none(opts, pool, profile=None):
    try:
        return get(opts, pool, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, pool, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", pool)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{pool}", body=body, profile=profile)


def delete(opts, pool, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{pool}", profile=profile)
