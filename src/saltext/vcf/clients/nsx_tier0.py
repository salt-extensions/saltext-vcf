"""Resource layer for NSX Tier-0 gateways (Policy API /infra/tier-0s)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/tier-0s"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, tier0, profile=None):
    return nsx.api_get(opts, f"{PATH}/{tier0}", profile=profile)


def get_or_none(opts, tier0, profile=None):
    try:
        return get(opts, tier0, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
