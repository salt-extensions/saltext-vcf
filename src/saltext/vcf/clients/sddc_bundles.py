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


def upload(opts, bundle_file_path, manifest_file_path, signature_file_path, profile=None):
    """Register an offline patch bundle already staged on SDDC Manager.

    All three paths are on the SDDC Manager appliance's local filesystem; the
    caller is responsible for having placed the ``.tar``, ``.manifest`` and
    ``.sig`` files there (that's the OFFLINE-mode step from the Async Patch
    Tool workflow). Returns the task id for the import.
    """
    body = {
        "bundleUploadSpec": {
            "bundleFilePath": bundle_file_path,
            "manifestFilePath": manifest_file_path,
            "signatureFilePath": signature_file_path,
        }
    }
    return sddc.api_post(opts, PATH, body=body, profile=profile)


def delete(opts, bundle_id, profile=None):
    """Delete a bundle from the SDDC Manager LCM repository."""
    return sddc.api_delete(opts, f"{PATH}/{bundle_id}", profile=profile)


def for_skip_upgrade(opts, domain_id, profile=None):
    """List bundles applicable to a skip-upgrade of *domain_id*."""
    return sddc.api_get(opts, f"{PATH}/domains/{domain_id}", profile=profile)
