"""Resource layer for NSX security groups (Policy API /infra/domains/default/groups)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/domains/default/groups"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, group, profile=None):
    return nsx.api_get(opts, f"{PATH}/{group}", profile=profile)


def get_or_none(opts, group, profile=None):
    try:
        return get(opts, group, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, group, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", group)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{group}", body=body, profile=profile)


def delete(opts, group, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{group}", profile=profile)
