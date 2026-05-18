"""NSX Load Balancer virtual server (Policy API /infra/lb-virtual-servers)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/lb-virtual-servers"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, virtual_server, profile=None):
    return nsx.api_get(opts, f"{PATH}/{virtual_server}", profile=profile)


def get_or_none(opts, virtual_server, profile=None):
    try:
        return get(opts, virtual_server, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, virtual_server, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", virtual_server)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{virtual_server}", body=body, profile=profile)


def delete(opts, virtual_server, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{virtual_server}", profile=profile)
