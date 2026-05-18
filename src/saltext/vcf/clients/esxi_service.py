"""ESXi services (TSM-SSH, ntpd, etc.) — list, get, control, startup policy."""

import requests

from saltext.vcf.utils import esxi

PATH = "/api/esx/services"

# Valid startup policies per the ESXi REST API
POLICIES = ("ON", "OFF", "AUTOMATIC")


def list_(opts, profile=None):
    return esxi.api_get(opts, PATH, profile=profile)


def get(opts, service, profile=None):
    return esxi.api_get(opts, f"{PATH}/{service}", profile=profile)


def get_or_none(opts, service, profile=None):
    try:
        return get(opts, service, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def start(opts, service, profile=None):
    return esxi.api_post(opts, f"{PATH}/{service}", params={"action": "start"}, profile=profile)


def stop(opts, service, profile=None):
    return esxi.api_post(opts, f"{PATH}/{service}", params={"action": "stop"}, profile=profile)


def restart(opts, service, profile=None):
    return esxi.api_post(opts, f"{PATH}/{service}", params={"action": "restart"}, profile=profile)


def set_policy(opts, service, policy, profile=None):
    """Set startup policy. *policy* in :data:`POLICIES`."""
    if policy not in POLICIES:
        raise ValueError(f"policy must be one of {POLICIES}, got {policy!r}")
    return esxi.api_patch(
        opts, f"{PATH}/{service}", body={"startup_policy": policy}, profile=profile
    )


def is_running(service_obj):
    """True when a service dict (from :func:`get`) reports running state."""
    return service_obj.get("state") == "RUNNING" or bool(service_obj.get("running"))
