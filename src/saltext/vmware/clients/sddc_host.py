"""Resource layer for SDDC Manager hosts (/v1/hosts)."""

import requests

from saltext.vmware.utils import sddc

PATH = "/v1/hosts"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, host, profile=None):
    return sddc.api_get(opts, f"{PATH}/{host}", profile=profile)


def get_or_none(opts, host, profile=None):
    try:
        return get(opts, host, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def commission(opts, host_specs, profile=None):
    return sddc.api_post(opts, PATH, body=host_specs, profile=profile)


def decommission(opts, host, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{host}", profile=profile)
