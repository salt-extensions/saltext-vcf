"""
Client for vCenter's ESX Lifecycle Manager (vLCM) REST API.

Patches ESXi hosts in a vSphere cluster via the desired-image workflow:
depots supply update payloads, a *desired image* draft is imported,
validated and committed against a base image (plus optional add-ons), an
apply policy controls remediation behavior (quick boot, DPM, HA), and the
scan/check/stage/apply actions drive compliance checking and remediation
against the cluster's committed software spec. Endpoints live under::

    /api/esx/settings/depots/...
    /api/esx/settings/clusters/{cluster_id}/software/...
    /api/esx/settings/clusters/{cluster_id}/policies/apply

All calls go through the vCenter session
(:mod:`saltext.vcf.utils.vcenter`), so the standard ``saltext.vcf.vcenter``
pillar config is what selects the target vCenter — no separate connection
config is needed for this domain. Mutating calls append ``vmw-task=true``
and return a vCenter CIS task id (a bare string, or ``{"value": "<id>"}``);
pass that response to :func:`wait_for_task` to block for completion.
"""

import json

import requests

from saltext.vcf.utils import vcenter

_DEPOTS = "/api/esx/settings/depots"
_CLUSTER = "/api/esx/settings/clusters/{cluster}"


def _cluster_path(cluster, suffix=""):
    return _CLUSTER.format(cluster=cluster) + suffix


def _compact(body):
    """Drop ``None``-valued keys so optional fields aren't sent at all."""
    return {k: v for k, v in (body or {}).items() if v is not None}


# ---------------------------------------------------------------------------
# Depots
# ---------------------------------------------------------------------------


def online_depot_list(opts, profile=None):
    """Return the list of configured online depots."""
    return vcenter.api_get(opts, f"{_DEPOTS}/online", profile=profile)


def online_depot_create(opts, body, profile=None):
    """Create an online depot. *body* carries at least a ``url``."""
    return vcenter.api_post(opts, f"{_DEPOTS}/online", body=_compact(body), profile=profile)


def online_depot_update(opts, depot_id, body, profile=None):
    """Update an existing online depot."""
    return vcenter.api_patch(
        opts, f"{_DEPOTS}/online/{depot_id}", body=_compact(body), profile=profile
    )


def offline_depot_list(opts, profile=None):
    """Return the list of configured offline depots."""
    return vcenter.api_get(opts, f"{_DEPOTS}/offline", profile=profile)


def offline_depot_get(opts, depot_id, profile=None):
    """Return a single offline depot."""
    return vcenter.api_get(opts, f"{_DEPOTS}/offline/{depot_id}", profile=profile)


def offline_depot_create(opts, body, profile=None):
    """Create an offline depot (task). *body* carries at least ``location``."""
    return vcenter.api_post(
        opts,
        f"{_DEPOTS}/offline",
        body=_compact(body),
        params={"vmw-task": "true"},
        profile=profile,
    )


def offline_depot_delete(opts, depot_id, profile=None):
    """Delete an offline depot (task)."""
    return vcenter.api_delete(
        opts, f"{_DEPOTS}/offline/{depot_id}", params={"vmw-task": "true"}, profile=profile
    )


def depot_sync(opts, profile=None):
    """Trigger a sync of all depots (task).

    Some vCenter builds don't expose this action and respond 404; that's
    reported back as ``{"skipped": True}`` rather than raised, since
    there's nothing to sync against on those builds.
    """
    try:
        return vcenter.api_post(
            opts, _DEPOTS, params={"action": "sync", "vmw-task": "true"}, profile=profile
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return {"skipped": True}
        raise


# ---------------------------------------------------------------------------
# Desired image
# ---------------------------------------------------------------------------


def desired_image_get(opts, cluster, profile=None):
    """Return the cluster's current desired image (committed software spec)."""
    return vcenter.api_get(opts, _cluster_path(cluster, "/software"), profile=profile)


def base_image_get(opts, cluster, profile=None):
    """Return the cluster's available base images."""
    return vcenter.api_get(opts, _cluster_path(cluster, "/software/base-image"), profile=profile)


def drafts_list(opts, cluster, profile=None):
    """Return the list of desired-image drafts on the cluster."""
    return vcenter.api_get(opts, _cluster_path(cluster, "/software/drafts"), profile=profile)


def draft_get(opts, cluster, draft_id, profile=None):
    """Return a single desired-image draft."""
    return vcenter.api_get(
        opts, _cluster_path(cluster, f"/software/drafts/{draft_id}"), profile=profile
    )


def draft_delete(opts, cluster, draft_id, profile=None):
    """Delete a desired-image draft."""
    return vcenter.api_delete(
        opts, _cluster_path(cluster, f"/software/drafts/{draft_id}"), profile=profile
    )


def draft_import_software_spec(opts, cluster, image_spec, profile=None):
    """Import *image_spec* (a vLCM software spec dict) as a new draft.

    Unlike the other draft/lifecycle actions, this one is not
    ``vmw-task``-based — it always completes synchronously and returns the
    new draft directly, so no ``vmw-task=true`` is sent.
    """
    body = {"source_type": "JSON_STRING", "software_spec": json.dumps(image_spec)}
    return vcenter.api_post(
        opts,
        _cluster_path(cluster, "/software/drafts"),
        body=body,
        params={"action": "import-software-spec"},
        profile=profile,
    )


def draft_validate(opts, cluster, draft_id, profile=None):
    """Validate a desired-image draft (task)."""
    return vcenter.api_post(
        opts,
        _cluster_path(cluster, f"/software/drafts/{draft_id}"),
        params={"action": "validate", "vmw-task": "true"},
        profile=profile,
    )


def draft_commit(opts, cluster, draft_id, message=None, profile=None):
    """Commit a desired-image draft (task), making it the cluster's desired image.

    Always sends the ``message`` field, defaulting to ``""`` — this vAPI
    action rejects a request with no ``Content-Type: application/json``
    body at all (400 Bad Request), even though *message* is optional.
    """
    return vcenter.api_post(
        opts,
        _cluster_path(cluster, f"/software/drafts/{draft_id}"),
        body={"message": message if message is not None else ""},
        params={"action": "commit", "vmw-task": "true"},
        profile=profile,
    )


# ---------------------------------------------------------------------------
# Apply policy
# ---------------------------------------------------------------------------


def apply_policy_get(opts, cluster, profile=None):
    """Return the cluster's remediation apply policy."""
    return vcenter.api_get(opts, _cluster_path(cluster, "/policies/apply"), profile=profile)


def apply_policy_set(opts, cluster, policy_spec, profile=None):
    """Replace the cluster's remediation apply policy."""
    return vcenter.api_put(
        opts, _cluster_path(cluster, "/policies/apply"), body=policy_spec, profile=profile
    )


# ---------------------------------------------------------------------------
# Lifecycle actions (compliance scan, precheck, stage, remediate)
# ---------------------------------------------------------------------------


def _lifecycle_action(opts, cluster, action, body=None, profile=None):
    return vcenter.api_post(
        opts,
        _cluster_path(cluster, "/software"),
        body=body,
        params={"action": action, "vmw-task": "true"},
        profile=profile,
    )


def compliance_scan(opts, cluster, commit="1", hosts=None, profile=None):
    """Scan the cluster for compliance against its desired image (task).

    *commit* selects which committed software spec to scan against
    (``"1"`` is the current one — this vAPI action requires the field, it
    doesn't default it server-side). *hosts*, if given, restricts the scan
    to those host ids; omitted means the whole cluster (sent as ``[]``).
    """
    body = {"commit": commit, "hosts": hosts if hosts is not None else []}
    return _lifecycle_action(opts, cluster, "scan", body=body, profile=profile)


def precheck(opts, cluster, commit="1", profile=None):
    """Run remediation prechecks on the cluster (task). See :func:`compliance_scan` on *commit*."""
    return _lifecycle_action(opts, cluster, "check", body={"commit": commit}, profile=profile)


def stage(opts, cluster, commit="1", hosts=None, profile=None):
    """Stage the desired image on cluster hosts (task). See :func:`compliance_scan`."""
    body = {"commit": commit, "hosts": hosts if hosts is not None else []}
    return _lifecycle_action(opts, cluster, "stage", body=body, profile=profile)


def remediate(opts, cluster, accept_eula=True, profile=None):
    """Remediate (apply the desired image to) the cluster (task).

    Unlike scan/precheck/stage, this action's body has no ``hosts`` field —
    remediation always targets the whole cluster.
    """
    return _lifecycle_action(
        opts, cluster, "apply", body={"accept_eula": accept_eula}, profile=profile
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def _report_or_none(opts, cluster, suffix, profile=None):
    try:
        return vcenter.api_get(
            opts, _cluster_path(cluster, f"/software/reports/{suffix}"), profile=profile
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def last_check_result(opts, cluster, profile=None):
    """Return the cluster's last compliance/precheck result, or ``None`` if none exists yet."""
    return _report_or_none(opts, cluster, "last-check-result", profile=profile)


def apply_impact_report(opts, cluster, profile=None):
    """Return the cluster's apply-impact report, or ``None`` if none exists yet."""
    return _report_or_none(opts, cluster, "apply-impact", profile=profile)


def last_apply_result(opts, cluster, profile=None):
    """Return the cluster's last apply (remediate) result, or ``None`` if none exists yet."""
    return _report_or_none(opts, cluster, "last-apply-result", profile=profile)


# ---------------------------------------------------------------------------
# Task polling
# ---------------------------------------------------------------------------


def _task_id(resp):
    """Extract a task id from a ``vmw-task=true`` response.

    Such responses are either a bare task-id string or ``{"value": "<id>"}``.
    """
    if isinstance(resp, dict) and "value" in resp:
        return resp["value"]
    return resp


def wait_for_task(opts, resp, timeout=1800, poll_interval=10, profile=None):
    """Block until the task referenced by *resp* (a ``vmw-task=true`` response) completes.

    Returns the final task dict. Raises ``RuntimeError`` if the task fails,
    or ``TimeoutError`` if it doesn't reach a terminal state within
    *timeout*. See :func:`saltext.vcf.utils.vcenter.wait_for_task`.
    """
    return vcenter.wait_for_task(
        opts, _task_id(resp), timeout=timeout, poll_interval=poll_interval, profile=profile
    )
