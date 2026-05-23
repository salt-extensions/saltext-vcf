"""VCF Automation — policies (``/policy/api/policies``).

VCFA policies are project- or org-scoped governance objects. Each has
a ``typeId`` that selects the policy semantics; common types are
``com.vmware.policy.approval``, ``com.vmware.policy.deployment.limit``,
``com.vmware.policy.deployment.lease``,
``com.vmware.policy.deployment.action``,
``com.vmware.policy.resource.quota``. The body shape varies by type;
this client passes through opaquely — callers are expected to know
which shape their ``typeId`` requires.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/policy/api/policies"
_TYPES = "/policy/api/types"


def list_(opts, project_id=None, profile=None):
    params = {}
    if project_id is not None:
        params["projectId"] = project_id
    resp = vcfa.api_get(opts, _BASE, params=params or None, profile=profile)
    return resp.get("content", []) or []


def get(opts, policy_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{policy_id}", profile=profile)


def get_or_none(opts, policy_id, profile=None):
    try:
        return get(opts, policy_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a policy.

    *spec* must include ``name``, ``typeId``, ``definition`` (the
    type-specific body), ``projectId`` or ``organizationId`` for scope.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, policy_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{policy_id}", body=spec, profile=profile)


def delete(opts, policy_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{policy_id}", profile=profile)


def list_types(opts, profile=None):
    """Return the set of policy ``typeId`` values the server supports."""
    resp = vcfa.api_get(opts, _TYPES, profile=profile)
    return resp.get("content", []) or []
