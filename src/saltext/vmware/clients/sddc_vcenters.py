"""SDDC Manager vCenter registrations (/v1/vcenters)."""

import requests

from saltext.vmware.utils import sddc

PATH = "/v1/vcenters"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, vcenter_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{vcenter_id}", profile=profile)


def get_or_none(opts, vcenter_id, profile=None):
    try:
        return get(opts, vcenter_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
