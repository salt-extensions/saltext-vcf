"""ESXi advanced system settings (kernel knobs exposed via the REST API)."""

import requests

from saltext.vcf.utils import esxi

PATH = "/api/esx/advanced"


def list_(opts, profile=None):
    return esxi.api_get(opts, PATH, profile=profile)


def get(opts, key, profile=None):
    return esxi.api_get(opts, f"{PATH}/{key}", profile=profile)


def get_or_none(opts, key, profile=None):
    try:
        return get(opts, key, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def set_value(opts, key, value, profile=None):
    return esxi.api_patch(opts, f"{PATH}/{key}", body={"value": value}, profile=profile)
