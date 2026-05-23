"""VCF Automation — custom roles (``/iam/api/roles``).

Custom roles bundle CSP service permissions into a named, assignable
unit. The role definitions live in the IAM service; bindings are
handled in :mod:`saltext.vcf.clients.vcfa_iam`.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/iam/api/roles"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("items", []) or resp.get("content", []) or []


def get(opts, role_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{role_id}", profile=profile)


def get_or_none(opts, role_id, profile=None):
    try:
        return get(opts, role_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a custom role.

    *spec* keys: ``name``, ``displayName``, ``description``,
    ``rolePermissions`` (list of CSP permission strings), ``orgId``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, role_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{role_id}", body=spec, profile=profile)


def delete(opts, role_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{role_id}", profile=profile)
