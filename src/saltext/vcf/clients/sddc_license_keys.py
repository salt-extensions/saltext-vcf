"""SDDC Manager license keys (/v1/license-keys)."""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/license-keys"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, license_key, profile=None):
    return sddc.api_get(opts, f"{PATH}/{license_key}", profile=profile)


def get_or_none(opts, license_key, profile=None):
    try:
        return get(opts, license_key, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def add(opts, key, product_type, description="", profile=None):
    """Register a license key with SDDC Manager.

    *product_type* is one of ``VCENTER``, ``VSAN``, ``NSXT``, ``SDDC_MANAGER``, etc.
    """
    spec = {"key": key, "productType": product_type, "description": description}
    return sddc.api_post(opts, PATH, body=spec, profile=profile)


def delete(opts, license_key, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{license_key}", profile=profile)


def licensing_info(opts, profile=None):
    """Return the licensing summary (limits, allocations) — separate endpoint."""
    return sddc.api_get(opts, "/v1/licensing-info", profile=profile)
