"""Resource layer for vCenter datacenters (/api/vcenter/datacenter)."""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/datacenter"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, datacenter, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{datacenter}", profile=profile)


def get_or_none(opts, datacenter, profile=None):
    try:
        return get(opts, datacenter, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, name, folder=None, profile=None):
    body = {"name": name}
    if folder is not None:
        body["folder"] = folder
    return vcenter.api_post(opts, PATH, body=body, profile=profile)


def delete(opts, datacenter, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{datacenter}", profile=profile)
