"""vCenter Supervisor Services catalog (VKS).

Supervisor Services are extensions installed on a Supervisor cluster
(TKG, Velero, Harbor, etc.). The catalog endpoint enumerates available
services and their installable versions.
"""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/namespace-management/supervisor-services"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, service_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{service_id}", profile=profile)


def get_or_none(opts, service_id, profile=None):
    try:
        return get(opts, service_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_versions(opts, service_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{service_id}/versions", profile=profile)


def get_version(opts, service_id, version, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{service_id}/versions/{version}", profile=profile)


def create(opts, service_spec, profile=None):
    """Register a Supervisor Service.

    *service_spec* per the vSphere REST API — typically a vSphereSupervisorServicesCreateSpec
    containing ``supervisor_service`` (id), ``content_type``, ``content``, and ``trusted``.
    """
    return vcenter.api_post(opts, PATH, body=service_spec, profile=profile)


def activate(opts, service_id, profile=None):
    """Transition a Supervisor Service to the ACTIVATED state."""
    return vcenter.api_post(
        opts, f"{PATH}/{service_id}", params={"action": "activate"}, profile=profile
    )


def deactivate(opts, service_id, profile=None):
    return vcenter.api_post(
        opts, f"{PATH}/{service_id}", params={"action": "deactivate"}, profile=profile
    )


def delete(opts, service_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{service_id}", profile=profile)
