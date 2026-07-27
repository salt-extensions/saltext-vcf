"""VCF Automation — org identity-provider registration (CSP gateway).

Register / delete external identity providers (AD, LDAP, SAML, OIDC)
against an org so operators can log in with directory-authenticated
accounts instead of the local ``configadmin``.

Endpoints (CSP ``am`` gateway; org-scoped)::

    GET    /csp/gateway/am/api/orgs/{orgId}/identity-providers
    GET    /csp/gateway/am/api/orgs/{orgId}/identity-providers/{idpId}
    POST   /csp/gateway/am/api/orgs/{orgId}/identity-providers
    PUT    /csp/gateway/am/api/orgs/{orgId}/identity-providers/{idpId}
    DELETE /csp/gateway/am/api/orgs/{orgId}/identity-providers/{idpId}

The IdP *spec* is passed through verbatim so callers can supply the
CSP JSON schema exactly as documented (types include ``AD``, ``LDAP``,
``OIDC``, ``SAML``; each type has its own required fields — bind DN,
URL, base DN, certificate PEM, etc.). :func:`find_by_name` walks the
list looking for a ``name`` match so idempotent states can look the
IdP up without persisting the server-side id.
"""

import requests

from saltext.vcf.utils import vcfa

_ORGS = "/csp/gateway/am/api/orgs"


def _base(org_id):
    return f"{_ORGS}/{org_id}/identity-providers"


def identity_provider_list(opts, org_id, *, profile=None):
    """Return the list of IdPs registered against *org_id*."""
    resp = vcfa.api_get(opts, _base(org_id), profile=profile)
    return resp.get("items", []) or resp.get("results", []) or resp.get("content", []) or []


def identity_provider_get(opts, org_id, idp_id, *, profile=None):
    return vcfa.api_get(opts, f"{_base(org_id)}/{idp_id}", profile=profile)


def identity_provider_get_or_none(opts, org_id, idp_id, *, profile=None):
    try:
        return identity_provider_get(opts, org_id, idp_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def find_by_name(opts, org_id, name, *, profile=None):
    """Return the IdP whose ``name`` matches, or ``None``."""
    for idp in identity_provider_list(opts, org_id, profile=profile):
        if idp.get("name") == name:
            return idp
    return None


def identity_provider_create(opts, org_id, spec, *, profile=None):
    """POST an IdP spec. *spec* is passed through as the body."""
    return vcfa.api_post(opts, _base(org_id), body=spec, profile=profile)


def identity_provider_update(opts, org_id, idp_id, spec, *, profile=None):
    """PUT an IdP spec."""
    return vcfa.api_put(opts, f"{_base(org_id)}/{idp_id}", body=spec, profile=profile)


def identity_provider_delete(opts, org_id, idp_id, *, profile=None):
    return vcfa.api_delete(opts, f"{_base(org_id)}/{idp_id}", profile=profile)
