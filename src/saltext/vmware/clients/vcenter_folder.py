"""vCenter folder (organizational hierarchy)."""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/folder"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, folder_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{folder_id}", profile=profile)


def get_or_none(opts, folder_id, profile=None):
    try:
        return get(opts, folder_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_by_type(opts, folder_type, profile=None):
    """``folder_type``: DATACENTER, DATASTORE, HOST, NETWORK, VIRTUAL_MACHINE."""
    return vcenter.api_get(opts, PATH, params={"type": folder_type}, profile=profile)
