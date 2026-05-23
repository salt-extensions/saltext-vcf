"""VCF Automation — projects (``/iaas/api/projects``).

A project is the central scoping unit in VCFA: catalog items,
deployments, ABX actions, policies, and quotas all belong to a
project. Membership lives on the project document itself as the four
role arrays ``administrators``, ``members``, ``viewers``,
``supervisors``; see :mod:`saltext.vcf.clients.vcfa_project_user` for
the membership-mutation helpers.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/iaas/api/projects"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("content", []) or []


def get(opts, project_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{project_id}", profile=profile)


def get_or_none(opts, project_id, profile=None):
    try:
        return get(opts, project_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a project.

    *spec* keys: ``name``, ``description``, ``zoneAssignmentConfigurations``
    (list of ``{zoneId, priority, maxNumberInstances, ...}``),
    ``administrators``, ``members``, ``viewers``, ``supervisors``,
    ``constraints``, ``properties``, ``operationTimeout``,
    ``sharedResources``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, project_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_BASE}/{project_id}", body=spec, profile=profile)


def delete(opts, project_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{project_id}", profile=profile)


def resources(opts, project_id, profile=None):
    """Return the resources currently provisioned against this project."""
    return vcfa.api_get(opts, f"{_BASE}/{project_id}/resources", profile=profile)
