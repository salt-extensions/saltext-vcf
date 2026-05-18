"""NSX Management API — RBAC role bindings (/api/v1/aaa/role-bindings)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/api/v1/aaa/role-bindings"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, binding_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{binding_id}", profile=profile)


def get_or_none(opts, binding_id, profile=None):
    try:
        return get(opts, binding_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, name, type_, roles, profile=None, **spec):
    """Create a role binding. *type_* is e.g. ``"remote_user"`` or ``"local_user"``.

    *roles* is a list of dicts like ``[{"role": "auditor"}]``.
    """
    body = {"name": name, "type": type_, "roles": list(roles)}
    body.update(spec)
    return nsx.api_post(opts, PATH, body=body, profile=profile)


def update(opts, binding_id, body, profile=None):
    return nsx.api_post(opts, f"{PATH}/{binding_id}", body=body, profile=profile)


def delete(opts, binding_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{binding_id}", profile=profile)
