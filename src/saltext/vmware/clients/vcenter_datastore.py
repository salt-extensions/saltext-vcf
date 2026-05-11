"""Client for vCenter datastores (/api/vcenter/datastore)."""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/datastore"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, datastore, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{datastore}", profile=profile)


def get_or_none(opts, datastore, profile=None):
    try:
        return get(opts, datastore, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
