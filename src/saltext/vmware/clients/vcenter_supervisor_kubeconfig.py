"""Supervisor-issued kubeconfig fetch (VKS).

On a Supervisor-enabled cluster, vCenter exposes a kubeconfig endpoint
that returns a YAML document an operator can hand to ``kubectl``,
``saltext-kubernetes``, or any standard Kubernetes client to talk to
the Supervisor API server.

The endpoint path matches the namespace-management v2 surface:

    GET /api/vcenter/namespaces/user/kubeconfig

with a per-cluster variant under
``/api/vcenter/namespace-management/clusters/{cluster}/kubeconfig`` on
recent vSphere builds. We try the cluster-scoped path first (deterministic
target) and fall back to the user-scoped one.

The response shape is ``{"kube_config": "<yaml>"}``; we return just the
YAML string for ergonomics.
"""

import requests

from saltext.vmware.utils import vcenter


def get_kubeconfig(opts, cluster_id, profile=None):
    """Return the kubeconfig YAML for *cluster_id*'s Supervisor.

    Tries the cluster-scoped endpoint first; falls back to the user-scoped
    endpoint when the cluster path is not exposed (older vSphere builds).
    """
    try:
        body = vcenter.api_get(
            opts,
            f"/api/vcenter/namespace-management/clusters/{cluster_id}/kubeconfig",
            profile=profile,
        )
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code not in (400, 404):
            raise
        body = vcenter.api_get(opts, "/api/vcenter/namespaces/user/kubeconfig", profile=profile)
    if isinstance(body, dict):
        return body.get("kube_config") or body.get("kubeconfig") or body
    return body


def get_kubeconfig_for_namespace(opts, namespace_id, profile=None):
    """Return a namespace-scoped kubeconfig (limits the user to one namespace)."""
    body = vcenter.api_get(
        opts,
        "/api/vcenter/namespaces/user/kubeconfig",
        params={"namespace": namespace_id},
        profile=profile,
    )
    if isinstance(body, dict):
        return body.get("kube_config") or body.get("kubeconfig") or body
    return body
