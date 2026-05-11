"""SDDC Manager upgrade workflows (/v1/upgrades)."""

import requests

from saltext.vmware.utils import sddc

PATH = "/v1/upgrades"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, upgrade_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{upgrade_id}", profile=profile)


def get_or_none(opts, upgrade_id, profile=None):
    try:
        return get(opts, upgrade_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def start(opts, upgrade_spec, profile=None):
    """Trigger an upgrade workflow. *upgrade_spec* per SDDC Manager API."""
    return sddc.api_post(opts, PATH, body=upgrade_spec, profile=profile)
