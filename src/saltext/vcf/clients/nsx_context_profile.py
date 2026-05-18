"""NSX layer-7 context profiles (/policy/api/v1/infra/context-profiles)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/context-profiles"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, profile_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{profile_id}", profile=profile)


def get_or_none(opts, profile_id, profile=None):
    try:
        return get(opts, profile_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, profile_id, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", profile_id)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{profile_id}", body=body, profile=profile)


def delete(opts, profile_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{profile_id}", profile=profile)
