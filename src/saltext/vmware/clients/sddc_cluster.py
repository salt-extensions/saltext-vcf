"""Resource layer for SDDC Manager clusters (/v1/clusters)."""

import requests

from saltext.vmware.utils import sddc

PATH = "/v1/clusters"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, cluster, profile=None):
    return sddc.api_get(opts, f"{PATH}/{cluster}", profile=profile)


def get_or_none(opts, cluster, profile=None):
    try:
        return get(opts, cluster, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, cluster_spec, profile=None):
    return sddc.api_post(opts, PATH, body=cluster_spec, profile=profile)


def delete(opts, cluster, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{cluster}", profile=profile)
