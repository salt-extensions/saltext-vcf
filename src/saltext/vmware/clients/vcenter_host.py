"""Resource layer for vCenter hosts (/api/vcenter/host)."""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/host"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, host, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{host}", profile=profile)


def get_or_none(opts, host, profile=None):
    try:
        return get(opts, host, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def enter_maintenance(opts, host, profile=None):
    return vcenter.api_post(
        opts,
        f"{PATH}/{host}",
        params={"action": "enter-maintenance-mode"},
        profile=profile,
    )


def exit_maintenance(opts, host, profile=None):
    return vcenter.api_post(
        opts,
        f"{PATH}/{host}",
        params={"action": "exit-maintenance-mode"},
        profile=profile,
    )


def is_in_maintenance(host_obj):
    """True if a host dict (as returned by :func:`get`) is in maintenance mode."""
    return host_obj.get("connection_state") == "MAINTENANCE" or bool(
        host_obj.get("in_maintenance_mode")
    )
