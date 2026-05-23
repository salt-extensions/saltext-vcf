"""VCF Automation — resource actions (``/form-service/api/custom/resource-actions``).

Resource actions are day-2 operations bound to a deployment resource
type (vSphere VM, NSX network, etc.). Each action either runs an ABX
action or kicks off a vRO workflow.

The API path is the legacy form-service surface; some VCFA versions
also expose this through ``/abx/api/resources/resource-actions`` —
this module sticks to the form-service path as canonical for 9.x.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/form-service/api/custom/resource-actions"


def list_(opts, project_id=None, profile=None):
    params = {"projects": project_id} if project_id else None
    resp = vcfa.api_get(opts, _BASE, params=params, profile=profile)
    return resp.get("content", []) or []


def get(opts, action_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{action_id}", profile=profile)


def get_or_none(opts, action_id, profile=None):
    try:
        return get(opts, action_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Register a resource action.

    *spec* keys: ``name``, ``displayName``, ``description``,
    ``projectId``, ``orgId``, ``resourceType`` (e.g.
    ``Cloud.vSphere.Machine``), ``runnableType``
    (``extensibility.abx`` / ``extensibility.vro``), ``runnableId``,
    ``inputParameters``, ``criteria``, ``formDefinition``, ``status``
    (``DRAFT`` / ``RELEASED``).
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, action_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{action_id}", body=spec, profile=profile)


def delete(opts, action_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{action_id}", profile=profile)
