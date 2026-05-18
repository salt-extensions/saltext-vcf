"""SDDC Manager network pools (/v1/network-pools)."""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/network-pools"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, pool_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{pool_id}", profile=profile)


def get_or_none(opts, pool_id, profile=None):
    try:
        return get(opts, pool_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, network_pool_spec, profile=None):
    """Create a network pool. *network_pool_spec* per the SDDC Manager API."""
    return sddc.api_post(opts, PATH, body=network_pool_spec, profile=profile)


def delete(opts, pool_id, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{pool_id}", profile=profile)
