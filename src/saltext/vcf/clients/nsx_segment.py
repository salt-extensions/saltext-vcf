"""Resource layer for NSX segments (Policy API /infra/segments)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/segments"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, segment, profile=None):
    return nsx.api_get(opts, f"{PATH}/{segment}", profile=profile)


def get_or_none(opts, segment, profile=None):
    try:
        return get(opts, segment, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, segment, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", segment)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{segment}", body=body, profile=profile)


def delete(opts, segment, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{segment}", profile=profile)
