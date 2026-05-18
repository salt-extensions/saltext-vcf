"""
Client for the vSphere 9 / VCF 9 cluster **Configuration Profile** API.

On vSphere 9, per-host imperative REST endpoints for services/firewall/NTP/
syslog/advanced settings do not exist. Configuration is instead expressed
declaratively at the cluster level via a JSON-schema-shaped *profile*; the
profile applies to every host in the cluster. The relevant endpoints live
under::

    /api/esx/settings/clusters/{cluster_id}/...

This module wraps the read/write surface of that API. All calls go through
the vCenter session (:mod:`saltext.vcf.utils.vcenter`), so the standard
``saltext.vcf.vcenter`` pillar config is what selects the target vCenter.

The cluster must be enabled for Configuration Profile (vLCM single-image
managed) for the configuration/draft endpoints to work; the
:func:`enablement_get` helper reports current status.
"""

import requests

from saltext.vcf.utils import vcenter

_BASE = "/api/esx/settings/clusters/{cluster}"


def _path(cluster, suffix=""):
    return _BASE.format(cluster=cluster) + suffix


def enablement_get(opts, cluster, profile=None):
    """Return ``{"enabled": bool, ...}`` for the cluster's CP enablement."""
    return vcenter.api_get(opts, _path(cluster, "/enablement/configuration"), profile=profile)


def schema_get(opts, cluster, profile=None):
    """Return the Configuration Profile JSON Schema for the cluster.

    The wrapper is ``{"schema": <schema-or-str>, "source": ...}``. When the
    schema field is a string, it's JSON-encoded — caller should ``json.loads``
    it.
    """
    return vcenter.api_get(opts, _path(cluster, "/configuration/schema"), profile=profile)


def configuration_get(opts, cluster, profile=None):
    """Return the currently applied configuration document for the cluster.

    Returns ``None`` if the cluster has no configuration applied yet (vCenter
    responds 400 with ``error_type=INVALID_ARGUMENT`` for clusters that are
    not vLCM-managed; we map that to ``None`` so callers can branch).
    """
    try:
        return vcenter.api_get(opts, _path(cluster, "/configuration"), profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


def drafts_list(opts, cluster, profile=None):
    """Return the list of configuration drafts on the cluster."""
    return vcenter.api_get(opts, _path(cluster, "/configuration/drafts"), profile=profile)


def draft_create(opts, cluster, body=None, profile=None):
    """Create a new draft. Returns the draft id (string).

    *body* may be a starter configuration document; if ``None``, an empty
    draft is created.
    """
    return vcenter.api_post(
        opts, _path(cluster, "/configuration/drafts"), body=body or {}, profile=profile
    )


def draft_get(opts, cluster, draft_id, profile=None):
    """Return the metadata + configuration of a single draft."""
    return vcenter.api_get(
        opts, _path(cluster, f"/configuration/drafts/{draft_id}"), profile=profile
    )


def draft_get_configuration(opts, cluster, draft_id, profile=None):
    """Return just the configuration body of a draft."""
    return vcenter.api_get(
        opts,
        _path(cluster, f"/configuration/drafts/{draft_id}/configuration"),
        profile=profile,
    )


def draft_update_configuration(opts, cluster, draft_id, body, profile=None):
    """Replace the configuration document inside *draft_id*."""
    return vcenter.api_patch(
        opts,
        _path(cluster, f"/configuration/drafts/{draft_id}/configuration"),
        body=body,
        profile=profile,
    )


def draft_delete(opts, cluster, draft_id, profile=None):
    return vcenter.api_delete(
        opts, _path(cluster, f"/configuration/drafts/{draft_id}"), profile=profile
    )


def draft_apply(opts, cluster, draft_id, profile=None):
    """Apply a draft (POST with ``?action=apply``). Returns the apply task id."""
    return vcenter.api_post(
        opts,
        _path(cluster, f"/configuration/drafts/{draft_id}"),
        params={"action": "apply"},
        profile=profile,
    )


def last_apply_result(opts, cluster, profile=None):
    """Return the last apply result for the cluster's configuration.

    Returns ``None`` when the cluster isn't yet under Configuration Profile
    management (vCenter responds 400 INVALID_ARGUMENT).
    """
    try:
        return vcenter.api_get(
            opts,
            _path(cluster, "/configuration/reports/last-apply-result"),
            profile=profile,
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


def last_compliance_result(opts, cluster, profile=None):
    try:
        return vcenter.api_get(
            opts,
            _path(cluster, "/configuration/reports/last-compliance-result"),
            profile=profile,
        )
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return None
        raise


# ---------------------------------------------------------------------------
# JSON-pointer-style helpers for poking at nested keys in a profile document
# ---------------------------------------------------------------------------


def get_profile_value(profile_doc, key_path):
    """Read a nested key from a Configuration Profile document.

    *key_path* is a dotted string like
    ``profile.esx.health.ntp_health.servers`` — matches the schema's
    ``properties/.../properties/...`` walk.
    """
    node = profile_doc
    for part in key_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def set_profile_value(profile_doc, key_path, value):
    """Write a nested key into a Configuration Profile document in place.

    Returns the modified document so callers can chain.
    """
    parts = key_path.split(".")
    node = profile_doc
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value
    return profile_doc
