"""VCF Automation — vRO packages (``/vco/api/packages``).

vRealize Orchestrator packages are the unit of vRO content
distribution. They wrap workflows, actions, configuration elements,
resources, and other vRO objects.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/vco/api/packages"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("link", []) or resp.get("content", []) or []


def get(opts, name, profile=None):
    """Return the package metadata for *name* (e.g. ``com.example.pkg``)."""
    return vcfa.api_get(opts, f"{_BASE}/{name}", profile=profile)


def get_or_none(opts, name, profile=None):
    try:
        return get(opts, name, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def import_(opts, name, package_bytes, *, overwrite=False, profile=None):
    """Import a ``.package`` file into vRO.

    *package_bytes* is the raw ``.package`` content. *name* is used as
    the multipart form field name only; the package's internal name
    comes from the file itself.
    """
    files = {"file": (f"{name}.package", package_bytes, "application/octet-stream")}
    params = {"overwrite": "true"} if overwrite else None
    return vcfa.api_post_multipart(opts, _BASE, files=files, params=params, profile=profile)


def delete(opts, name, *, option=None, profile=None):
    """Delete a vRO package.

    *option* one of ``deletePackage`` (just the package),
    ``deletePackageWithContent`` (and its content),
    ``deletePackageKeepingShared`` (default behavior).
    """
    params = {"option": option} if option else None
    return vcfa.api_delete(opts, f"{_BASE}/{name}", params=params, profile=profile)


def export_(opts, name, profile=None):
    """Return the raw ``.package`` bytes for *name*."""
    resp = vcfa._request("GET", opts, f"{_BASE}/{name}", profile=profile)
    return resp.content
