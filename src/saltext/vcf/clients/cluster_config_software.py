"""
vLCM single-image software lifecycle for a cluster.

Where :mod:`saltext.vcf.clients.cluster_config` wraps the
*Configuration Profile* half of ``/api/esx/settings/clusters/{id}/...``,
this module wraps the *software image* half — the surface that
remediates ESXi version + add-on + components + firmware. The two
sides share the same vCenter session
(:mod:`saltext.vcf.utils.vcenter`).

Workflow at a glance:

1. Read the cluster's desired image with :func:`get`.
2. Make changes through a draft: :func:`draft_create` →
   :func:`draft_update_base_image` / ``add_component`` / …
3. Commit the draft to make it the new desired image
   (:func:`draft_commit`).
4. Pre-check: :func:`check`.
5. Optionally stage payloads to hosts ahead of time:
   :func:`stage`.
6. Apply: :func:`apply`. Both ``check`` and ``apply`` return a vCenter
   task id; poll via :func:`saltext.vcf.utils.vim.wait_for_task` or
   the corresponding ``last_*_result`` reader below.

All endpoints live under
``/api/esx/settings/clusters/{cluster}/software``.
"""

import requests

from saltext.vcf.utils import vcenter

_BASE = "/api/esx/settings/clusters/{cluster}/software"


def _path(cluster, suffix=""):
    return _BASE.format(cluster=cluster) + suffix


# ---------------------------------------------------------------------------
# Desired image (read-only on the live spec)
# ---------------------------------------------------------------------------


def get(opts, cluster, profile=None):
    """Return the current desired software image for the cluster.

    Returns ``None`` if the cluster isn't using single-image (e.g. still
    on baselines) — vCenter responds 400 ``INVALID_ARGUMENT`` in that
    case.
    """
    try:
        return vcenter.api_get(opts, _path(cluster), profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


def effective_components(opts, cluster, profile=None):
    """Return the components currently in effect across the cluster."""
    return vcenter.api_get(opts, _path(cluster, "/effective-components"), profile=profile)


def solutions(opts, cluster, profile=None):
    """Return the registered solutions (e.g. vSAN) layered into the image."""
    return vcenter.api_get(opts, _path(cluster, "/solutions"), profile=profile)


# ---------------------------------------------------------------------------
# Drafts — the only way to change the desired image
# ---------------------------------------------------------------------------


def drafts_list(opts, cluster, profile=None):
    return vcenter.api_get(opts, _path(cluster, "/drafts"), profile=profile)


def draft_get(opts, cluster, draft_id, profile=None):
    return vcenter.api_get(opts, _path(cluster, f"/drafts/{draft_id}"), profile=profile)


def draft_create(opts, cluster, profile=None):
    """Open a fresh draft seeded from the current desired image. Returns the draft id."""
    return vcenter.api_post(opts, _path(cluster, "/drafts"), body={}, profile=profile)


def draft_delete(opts, cluster, draft_id, profile=None):
    return vcenter.api_delete(opts, _path(cluster, f"/drafts/{draft_id}"), profile=profile)


def draft_update_base_image(opts, cluster, draft_id, version, profile=None):
    """Set the ESXi base-image version (e.g. ``8.0.3-23299997``)."""
    return vcenter.api_put(
        opts,
        _path(cluster, f"/drafts/{draft_id}/software/base-image"),
        body={"version": version},
        profile=profile,
    )


def draft_set_add_on(opts, cluster, draft_id, name, version, profile=None):
    """Set the vendor add-on (e.g. ``Dell-Addon``, ``HPE-Addon``)."""
    return vcenter.api_put(
        opts,
        _path(cluster, f"/drafts/{draft_id}/software/add-on"),
        body={"name": name, "version": version},
        profile=profile,
    )


def draft_remove_add_on(opts, cluster, draft_id, profile=None):
    return vcenter.api_delete(
        opts, _path(cluster, f"/drafts/{draft_id}/software/add-on"), profile=profile
    )


def draft_set_component(opts, cluster, draft_id, component_name, version, profile=None):
    """Pin a component version into the draft."""
    return vcenter.api_put(
        opts,
        _path(cluster, f"/drafts/{draft_id}/software/components/{component_name}"),
        body={"version": version},
        profile=profile,
    )


def draft_remove_component(opts, cluster, draft_id, component_name, profile=None):
    return vcenter.api_delete(
        opts,
        _path(cluster, f"/drafts/{draft_id}/software/components/{component_name}"),
        profile=profile,
    )


def draft_set_hardware_support(opts, cluster, draft_id, packages, profile=None):
    """Set the firmware/hardware-support package spec.

    *packages* is the dict shape vCenter expects:
    ``{"packages": {"<vendor>": {"pkg": "...", "version": "..."}}}``.
    """
    return vcenter.api_put(
        opts,
        _path(cluster, f"/drafts/{draft_id}/software/hardware-support"),
        body=packages,
        profile=profile,
    )


def draft_commit(opts, cluster, draft_id, profile=None):
    """Commit a draft, making it the cluster's desired image.

    Returns the new commit id.
    """
    return vcenter.api_post(
        opts,
        _path(cluster, f"/drafts/{draft_id}/commits"),
        body={},
        profile=profile,
    )


# ---------------------------------------------------------------------------
# Actions on the live desired image
# ---------------------------------------------------------------------------


def check(opts, cluster, profile=None):
    """Run a pre-check. Returns a vCenter task id; poll with utils.vim.wait_for_task."""
    return vcenter.api_post(
        opts, _path(cluster), params={"action": "check"}, body={}, profile=profile
    )


def stage(opts, cluster, hosts=None, profile=None):
    """Pre-stage payloads on hosts. *hosts* optional list of host ids.

    Returns a vCenter task id.
    """
    body = {"hosts": list(hosts)} if hosts else {}
    return vcenter.api_post(
        opts, _path(cluster), params={"action": "stage"}, body=body, profile=profile
    )


def apply(opts, cluster, *, accept_eula=True, profile=None):
    """Apply the desired image to the cluster.

    Returns a vCenter task id. *accept_eula* maps to ``commit_spec``'s
    EULA flag — set to ``False`` if your workflow gates EULAs elsewhere.
    """
    body = {"commit_spec": {"accept_eula": bool(accept_eula)}}
    return vcenter.api_post(
        opts, _path(cluster), params={"action": "apply"}, body=body, profile=profile
    )


def scan(opts, cluster, profile=None):
    """Run a compliance scan. Returns a vCenter task id."""
    return vcenter.api_post(
        opts, _path(cluster), params={"action": "scan"}, body={}, profile=profile
    )


# ---------------------------------------------------------------------------
# Reports — read the outcome of the last apply / check / scan
# ---------------------------------------------------------------------------


def last_apply_result(opts, cluster, profile=None):
    try:
        return vcenter.api_get(opts, _path(cluster, "/reports/last-apply-result"), profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


def last_check_result(opts, cluster, profile=None):
    try:
        return vcenter.api_get(opts, _path(cluster, "/reports/last-check-result"), profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


def last_compliance_result(opts, cluster, profile=None):
    try:
        return vcenter.api_get(
            opts, _path(cluster, "/reports/last-compliance-result"), profile=profile
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


def last_stage_result(opts, cluster, profile=None):
    try:
        return vcenter.api_get(opts, _path(cluster, "/reports/last-stage-result"), profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise
