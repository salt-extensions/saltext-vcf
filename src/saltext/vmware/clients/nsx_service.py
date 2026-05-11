"""NSX service definitions (/policy/api/v1/infra/services)."""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/services"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, service, profile=None):
    return nsx.api_get(opts, f"{PATH}/{service}", profile=profile)


def get_or_none(opts, service, profile=None):
    try:
        return get(opts, service, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, service, profile=None, **spec):
    """Create or update a service (PUT). Include ``service_entries`` list."""
    body = {"display_name": spec.pop("display_name", service)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{service}", body=body, profile=profile)


def delete(opts, service, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{service}", profile=profile)
