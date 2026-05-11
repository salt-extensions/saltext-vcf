"""NSX Load Balancer persistence profiles (Policy API /infra/lb-persistence-profiles)."""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/lb-persistence-profiles"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, persistence, profile=None):
    return nsx.api_get(opts, f"{PATH}/{persistence}", profile=profile)


def get_or_none(opts, persistence, profile=None):
    try:
        return get(opts, persistence, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, persistence, resource_type, profile=None, **spec):
    """*resource_type*: ``LBSourceIpPersistenceProfile`` | ``LBCookiePersistenceProfile`` |
    ``LBGenericPersistenceProfile``.
    """
    body = {
        "resource_type": resource_type,
        "display_name": spec.pop("display_name", persistence),
    }
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{persistence}", body=body, profile=profile)


def delete(opts, persistence, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{persistence}", profile=profile)
