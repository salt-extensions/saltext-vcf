"""Supervisor cluster software/lifecycle (VKS).

Manages the Kubernetes version of a Supervisor cluster — list of
available versions, current version, upgrade triggering.
"""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/namespace-management/software/clusters"


def list_(opts, profile=None):
    """List Supervisor cluster software states."""
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, cluster_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{cluster_id}", profile=profile)


def get_or_none(opts, cluster_id, profile=None):
    try:
        return get(opts, cluster_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def upgrade(opts, cluster_id, upgrade_spec, profile=None):
    """Trigger a Supervisor version upgrade.

    *upgrade_spec* example::

        {"desired_version": "v1.28.2+vmware.1-vsc0.1.16-22674057", "ignore_precheck_warnings": false}
    """
    return vcenter.api_post(
        opts,
        f"{PATH}/{cluster_id}",
        params={"action": "upgrade"},
        body=upgrade_spec,
        profile=profile,
    )
