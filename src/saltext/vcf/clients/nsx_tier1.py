"""Resource layer for NSX Tier-1 gateways (Policy API /infra/tier-1s)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/tier-1s"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, tier1, profile=None):
    return nsx.api_get(opts, f"{PATH}/{tier1}", profile=profile)


def get_or_none(opts, tier1, profile=None):
    try:
        return get(opts, tier1, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, tier1, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", tier1)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{tier1}", body=body, profile=profile)


def delete(opts, tier1, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{tier1}", profile=profile)
