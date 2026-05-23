"""VCF Automation — IAM (CSP gateway-side identity).

The CSP gateway exposes org-level identity primitives: organizations,
users, and the role bindings between them. This client targets the
role-binding surface (the "IAM configuration" most operators care
about); see :mod:`saltext.vcf.clients.vcfa_custom_role` for role
definitions.

Endpoints:

* ``GET    /csp/gateway/am/api/loggedin/user/orgs``            — orgs the caller can see
* ``GET    /csp/gateway/am/api/orgs/{orgId}``                  — org metadata
* ``GET    /csp/gateway/am/api/orgs/{orgId}/users``            — org users
* ``GET    /csp/gateway/am/api/orgs/{orgId}/users/{userId}/roles`` — a user's roles
* ``PATCH  /csp/gateway/am/api/orgs/{orgId}/users/{userId}/roles`` — add/remove bindings
"""

import requests

from saltext.vcf.utils import vcfa

_ORGS = "/csp/gateway/am/api/orgs"
_LOGGED_IN_ORGS = "/csp/gateway/am/api/loggedin/user/orgs"


def list_orgs(opts, profile=None):
    """Return the orgs visible to the authenticated caller."""
    resp = vcfa.api_get(opts, _LOGGED_IN_ORGS, profile=profile)
    return resp.get("items", []) or resp.get("content", []) or []


def get_org(opts, org_id, profile=None):
    return vcfa.api_get(opts, f"{_ORGS}/{org_id}", profile=profile)


def get_org_or_none(opts, org_id, profile=None):
    try:
        return get_org(opts, org_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_users(opts, org_id, profile=None):
    resp = vcfa.api_get(opts, f"{_ORGS}/{org_id}/users", profile=profile)
    return resp.get("items", []) or resp.get("results", []) or []


def get_user_roles(opts, org_id, user_id, profile=None):
    """Return the role-binding list for *user_id* in *org_id*."""
    return vcfa.api_get(opts, f"{_ORGS}/{org_id}/users/{user_id}/roles", profile=profile)


def patch_user_roles(opts, org_id, user_id, *, add=None, remove=None, profile=None):
    """Mutate role bindings via the CSP patch endpoint.

    *add* and *remove* are lists of ``{name, resource}`` role
    references. Either or both may be supplied; an empty patch is
    rejected by the server.
    """
    body = {}
    if add:
        body["rolesToAdd"] = list(add)
    if remove:
        body["rolesToRemove"] = list(remove)
    if not body:
        raise ValueError("patch_user_roles requires at least one of add= or remove=")
    return vcfa.api_patch(
        opts, f"{_ORGS}/{org_id}/users/{user_id}/roles", body=body, profile=profile
    )
