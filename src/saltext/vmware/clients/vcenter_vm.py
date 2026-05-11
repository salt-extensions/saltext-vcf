"""Resource layer for vCenter VMs (/api/vcenter/vm)."""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/vm"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, vm, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{vm}", profile=profile)


def get_or_none(opts, vm, profile=None):
    try:
        return get(opts, vm, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def _power(opts, vm, action, profile=None):
    return vcenter.api_post(opts, f"{PATH}/{vm}/power", params={"action": action}, profile=profile)


def power_on(opts, vm, profile=None):
    return _power(opts, vm, "start", profile=profile)


def power_off(opts, vm, profile=None):
    return _power(opts, vm, "stop", profile=profile)


def reset(opts, vm, profile=None):
    return _power(opts, vm, "reset", profile=profile)
