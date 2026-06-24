"""Resource layer for vCenter datacenters (/api/vcenter/datacenter)."""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/datacenter"
FOLDER_PATH = "/api/vcenter/folder"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, datacenter, profile=None):
    """Get a datacenter by its managed object id (e.g. ``datacenter-1``)."""
    return vcenter.api_get(opts, f"{PATH}/{datacenter}", profile=profile)


def get_or_none(opts, datacenter, profile=None):
    """Get a datacenter by managed-object id, returning ``None`` on 404."""
    try:
        return get(opts, datacenter, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_by_name(opts, name, profile=None):
    """Return the datacenter summary matching *name*, or ``None``.

    The vCenter REST API addresses datacenters by managed-object id, not by
    display name, so existence checks by name must go through the list endpoint
    with a ``names`` filter rather than ``GET /datacenter/{name}`` (which would
    404 for any real display name and break idempotency).
    """
    results = vcenter.api_get(opts, PATH, params={"names": name}, profile=profile)
    if isinstance(results, list) and results:
        return results[0]
    return None


def _default_datacenter_folder(opts, profile=None):
    """Return a folder MoID suitable for creating a datacenter.

    vCenter's ``POST /datacenter`` currently requires the ``folder`` field. When
    the caller does not supply one, pick the first DATACENTER-type folder.
    """
    folders = vcenter.api_get(opts, FOLDER_PATH, params={"type": "DATACENTER"}, profile=profile)
    if isinstance(folders, list) and folders:
        return folders[0]["folder"]
    raise ValueError(
        "No DATACENTER-type folder found in vCenter; cannot determine a parent "
        "folder for datacenter creation. Pass an explicit 'folder' MoID."
    )


def create(opts, name, folder=None, profile=None):
    if folder is None:
        folder = _default_datacenter_folder(opts, profile=profile)
    body = {"name": name, "folder": folder}
    return vcenter.api_post(opts, PATH, body=body, profile=profile)


def delete(opts, datacenter, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{datacenter}", profile=profile)
