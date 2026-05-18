"""SDDC Manager software bundles (/v1/bundles)."""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/bundles"


def list_(opts, profile=None):
    return sddc.api_get(opts, PATH, profile=profile)


def get(opts, bundle_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{bundle_id}", profile=profile)


def get_or_none(opts, bundle_id, profile=None):
    try:
        return get(opts, bundle_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def download(opts, bundle_id, profile=None):
    """Trigger a bundle download. Returns the task id."""
    return sddc.api_patch(
        opts,
        f"{PATH}/{bundle_id}",
        body={"bundleDownloadSpec": {"downloadNow": True}},
        profile=profile,
    )
