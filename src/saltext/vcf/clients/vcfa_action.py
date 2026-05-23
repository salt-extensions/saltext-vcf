"""VCF Automation — ABX actions (``/abx/api/resources/actions``).

ABX (Action Based Extensibility) actions are serverless code (Python,
Node, PowerShell) that VCFA invokes either on demand (catalog item)
or via event subscriptions (post-provisioning, etc.).
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/abx/api/resources/actions"


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
    """Create an ABX action.

    *spec* keys: ``name``, ``description``, ``projectId``, ``orgId``,
    ``runtime`` (``python``/``nodejs``/``powershell``), ``entrypoint``,
    ``source`` (the inline code), ``inputs``, ``shared``, ``system``,
    ``timeoutSeconds``, ``memoryInMB``, ``dependencies``,
    ``actionType``, ``provider``, ``faasProvider``, ``cpuShares``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, action_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{action_id}", body=spec, profile=profile)


def delete(opts, action_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{action_id}", profile=profile)


def run(opts, action_id, inputs=None, profile=None):
    """Invoke an action on demand. Returns the action-run record."""
    body = {"inputs": inputs or {}}
    return vcfa.api_post(opts, f"{_BASE}/{action_id}/run", body=body, profile=profile)


def list_runs(opts, action_id, profile=None):
    resp = vcfa.api_get(opts, f"{_BASE}/{action_id}/action-runs", profile=profile)
    return resp.get("content", []) or []
