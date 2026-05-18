"""VCF Installer log bundle generation."""

import requests

from saltext.vcf.utils import installer


def list_(opts, profile=None):
    """Return all log bundles known to the installer."""
    return installer.api_get(opts, "/v1/system/log-bundles", profile=profile)


def get(opts, bundle_id, profile=None):
    return installer.api_get(opts, f"/v1/system/log-bundles/{bundle_id}", profile=profile)


def get_or_none(opts, bundle_id, profile=None):
    try:
        return get(opts, bundle_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def generate(opts, profile=None, **spec):
    """Trigger generation of a new log bundle. Returns the task dict."""
    return installer.api_post(opts, "/v1/system/log-bundles", body=spec or None, profile=profile)


def delete(opts, bundle_id, profile=None):
    return installer.api_delete(opts, f"/v1/system/log-bundles/{bundle_id}", profile=profile)
