"""VCF Automation — cloud templates (``/blueprint/api/blueprints``).

Cloud templates are the VCFA-era rebrand of vRA blueprints. The
underlying API still uses ``blueprint`` everywhere. Each template is
versioned independently; versions are released to the catalog so
end-users can request deployments from them.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/blueprint/api/blueprints"


def list_(opts, project_id=None, profile=None):
    params = {}
    if project_id is not None:
        params["projects"] = project_id
    resp = vcfa.api_get(opts, _BASE, params=params or None, profile=profile)
    return resp.get("content", []) or []


def get(opts, blueprint_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{blueprint_id}", profile=profile)


def get_or_none(opts, blueprint_id, profile=None):
    try:
        return get(opts, blueprint_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a blueprint.

    *spec* keys: ``name``, ``description``, ``projectId``, ``content``
    (the YAML/JSON template body), ``requestScopeOrg``,
    ``contentSourceId``, ``contentSourcePath``, ``contentSourceType``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, blueprint_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{blueprint_id}", body=spec, profile=profile)


def delete(opts, blueprint_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{blueprint_id}", profile=profile)


def list_versions(opts, blueprint_id, profile=None):
    resp = vcfa.api_get(opts, f"{_BASE}/{blueprint_id}/versions", profile=profile)
    return resp.get("content", []) or []


def get_version(opts, blueprint_id, version_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{blueprint_id}/versions/{version_id}", profile=profile)


def create_version(opts, blueprint_id, spec, profile=None):
    """Release a blueprint version.

    *spec* keys: ``version`` (e.g. ``"1.0"``), ``description``,
    ``changeLog``, ``release`` (``true`` to publish to the catalog
    immediately).
    """
    return vcfa.api_post(opts, f"{_BASE}/{blueprint_id}/versions", body=spec, profile=profile)


def release_version(opts, blueprint_id, version_id, profile=None):
    """Release an existing version to the catalog."""
    return vcfa.api_post(
        opts, f"{_BASE}/{blueprint_id}/versions/{version_id}/actions/release", profile=profile
    )


def unrelease_version(opts, blueprint_id, version_id, profile=None):
    return vcfa.api_post(
        opts, f"{_BASE}/{blueprint_id}/versions/{version_id}/actions/unrelease", profile=profile
    )
