"""VCF Automation — ABX action secrets (``/abx/api/resources/action-secrets``).

Action secrets are scoped credentials/strings ABX actions reference at
runtime. They're write-once-read-never from the API.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/abx/api/resources/action-secrets"


def list_(opts, project_id=None, profile=None):
    params = {"projects": project_id} if project_id else None
    resp = vcfa.api_get(opts, _BASE, params=params, profile=profile)
    return resp.get("content", []) or []


def get(opts, secret_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{secret_id}", profile=profile)


def get_or_none(opts, secret_id, profile=None):
    try:
        return get(opts, secret_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create an action secret.

    *spec* keys: ``name``, ``value``, ``orgId``, ``projectId``,
    ``encrypted`` (bool).
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, secret_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{secret_id}", body=spec, profile=profile)


def delete(opts, secret_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{secret_id}", profile=profile)
