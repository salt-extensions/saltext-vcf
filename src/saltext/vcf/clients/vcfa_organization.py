"""VCF Automation — tenants / organizations (CSP gateway).

Organizations are the top-level tenancy boundary in VCFA / Aria
Automation 9.x. Every project, catalog item, cloud-account, and role
binding is scoped inside an org. This client owns the org lifecycle
(create / read / update / delete) and the service-definition
attach-points that determine which VCFA microservices the org can
consume.

For per-user role bindings inside an org see
:mod:`saltext.vcf.clients.vcfa_iam`; for the per-project membership
arrays see :mod:`saltext.vcf.clients.vcfa_project_user`.

Endpoints (CSP gateway):

* ``GET    /csp/gateway/am/api/orgs``                                 — list orgs
* ``GET    /csp/gateway/am/api/orgs/{orgId}``                         — get one
* ``POST   /csp/gateway/am/api/orgs``                                 — create tenant
* ``PATCH  /csp/gateway/am/api/orgs/{orgId}``                         — update
* ``DELETE /csp/gateway/am/api/orgs/{orgId}``                         — delete
* ``GET    /csp/gateway/am/api/orgs/{orgId}/service-definitions``     — list attached services
* ``POST   /csp/gateway/am/api/orgs/{orgId}/service-definitions``     — enable a service
* ``DELETE /csp/gateway/am/api/orgs/{orgId}/service-definitions/{id}`` — disable a service
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/csp/gateway/am/api/orgs"


def list_(opts, profile=None):
    """List all orgs the caller can see.

    The CSP gateway returns the collection under either ``items`` or
    ``content`` depending on release; we normalise both.
    """
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("items", []) or resp.get("content", []) or []


def get(opts, org_id, profile=None):
    """Get one org by id."""
    return vcfa.api_get(opts, f"{_BASE}/{org_id}", profile=profile)


def get_or_none(opts, org_id, profile=None):
    """Get one org by id, or ``None`` on 404."""
    try:
        return get(opts, org_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a new tenant / organization.

    *spec* keys: ``displayName`` (required), ``description``, ``name``
    (short slug), plus any tenant-specific properties the deployment
    accepts (``parentRefLink``, ``customPropertyGroups`` etc.).
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, org_id, spec, profile=None):
    """Patch an existing org."""
    return vcfa.api_patch(opts, f"{_BASE}/{org_id}", body=spec, profile=profile)


def delete(opts, org_id, profile=None):
    """Delete an org."""
    return vcfa.api_delete(opts, f"{_BASE}/{org_id}", profile=profile)


def list_services(opts, org_id, profile=None):
    """List service definitions attached to *org_id*."""
    resp = vcfa.api_get(opts, f"{_BASE}/{org_id}/service-definitions", profile=profile)
    return resp.get("items", []) or resp.get("content", []) or []


def enable_service(opts, org_id, service_definition_id, profile=None):
    """Enable *service_definition_id* on the org.

    The gateway accepts either ``{"serviceDefinitionId": "..."}`` or
    ``{"serviceDefinitionLink": "..."}``; we send the id form.
    """
    body = {"serviceDefinitionId": service_definition_id}
    return vcfa.api_post(opts, f"{_BASE}/{org_id}/service-definitions", body=body, profile=profile)


def disable_service(opts, org_id, service_definition_id, profile=None):
    """Detach *service_definition_id* from the org."""
    return vcfa.api_delete(
        opts,
        f"{_BASE}/{org_id}/service-definitions/{service_definition_id}",
        profile=profile,
    )
