"""NSX Load Balancer service (Policy API /infra/lb-services)."""

import requests

from saltext.vmware.utils import nsx

PATH = "/policy/api/v1/infra/lb-services"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, lb_service, profile=None):
    return nsx.api_get(opts, f"{PATH}/{lb_service}", profile=profile)


def get_or_none(opts, lb_service, profile=None):
    try:
        return get(opts, lb_service, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, lb_service, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", lb_service)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{lb_service}", body=body, profile=profile)


def delete(opts, lb_service, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{lb_service}", profile=profile)
