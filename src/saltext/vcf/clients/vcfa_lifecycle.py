"""VCF Automation lifecycle management (``/lcm/api/...``).

VCFA's embedded LCM tracks installed-product versions, manages
upgrade requests, and keeps system snapshots that operators can roll
back to. Auth is the same VCFA bearer-token surface used by every
``vcfa_*`` client (:mod:`saltext.vcf.utils.vcfa`).

Endpoints wrapped here (paths may vary slightly between minor
versions of VCFA; ``/lcm/api/v1`` and ``/lcm/api/v2`` are both seen
in the wild — this module sticks to the unversioned form which the
gateway routes to the current default):

* ``GET    /lcm/api/products``                      — installed product catalog
* ``GET    /lcm/api/products/{productId}``          — one product
* ``GET    /lcm/api/products/{productId}/versions`` — installed + available versions
* ``GET    /lcm/api/products/{productId}/patches``  — installed + available patches
* ``GET    /lcm/api/upgrades``                      — list upgrade requests
* ``GET    /lcm/api/upgrades/{upgradeId}``          — one upgrade request
* ``POST   /lcm/api/upgrades``                      — start an upgrade
* ``POST   /lcm/api/upgrades/{upgradeId}/actions``  — cancel / retry / resume
* ``GET    /lcm/api/snapshots``                     — list system snapshots
* ``GET    /lcm/api/snapshots/{snapshotId}``        — one snapshot
* ``POST   /lcm/api/snapshots``                     — create a snapshot
* ``DELETE /lcm/api/snapshots/{snapshotId}``        — delete a snapshot
* ``POST   /lcm/api/snapshots/{snapshotId}/restore``— restore a snapshot

Patch-baseline management
-------------------------

VCFA's LCM exposes patches as a specialisation of a product version
(``patches`` sub-collection with ``status``: ``INSTALLED`` /
``AVAILABLE`` / ``STAGED``). Not every VCFA build surfaces a
``/patches`` endpoint — on builds that don't, callers fall back to
:func:`list_versions` and filter for ``kind == "PATCH"``.
:func:`installed_patches` / :func:`available_patches` implement that
fallback transparently.

For compliance workflows ("installed patch must be in an approved
baseline") the enforcement side is typically an ITIL policy external
to VCFA — the allowed list is passed by the caller and compared
against :func:`installed_patches` output. See
:func:`is_patch_allowed` / :func:`resolve_patch_version`.
"""

import time

import requests

from saltext.vcf.utils import vcfa

_PRODUCTS = "/lcm/api/products"
_UPGRADES = "/lcm/api/upgrades"
_SNAPSHOTS = "/lcm/api/snapshots"

# Terminal upgrade states. VCFA's controller surfaces a handful of
# different strings across versions; the conservative set below covers
# both modern (``SUCCEEDED`` / ``FAILED``) and legacy (``COMPLETED`` /
# ``ERROR``) variants.
_TERMINAL_OK = {"SUCCEEDED", "COMPLETED"}
_TERMINAL_BAD = {"FAILED", "ERROR", "CANCELED", "CANCELLED"}


# ---------------------------------------------------------------------------
# Products + versions
# ---------------------------------------------------------------------------


def list_products(opts, profile=None):
    resp = vcfa.api_get(opts, _PRODUCTS, profile=profile)
    return resp.get("content", []) or resp.get("items", []) or []


def get_product(opts, product_id, profile=None):
    return vcfa.api_get(opts, f"{_PRODUCTS}/{product_id}", profile=profile)


def get_product_or_none(opts, product_id, profile=None):
    try:
        return get_product(opts, product_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_versions(opts, product_id, profile=None):
    """Return installed + available versions for *product_id*."""
    resp = vcfa.api_get(opts, f"{_PRODUCTS}/{product_id}/versions", profile=profile)
    return resp.get("content", []) or resp.get("items", []) or []


# ---------------------------------------------------------------------------
# Upgrades
# ---------------------------------------------------------------------------


def list_upgrades(opts, profile=None):
    resp = vcfa.api_get(opts, _UPGRADES, profile=profile)
    return resp.get("content", []) or resp.get("items", []) or []


def get_upgrade(opts, upgrade_id, profile=None):
    return vcfa.api_get(opts, f"{_UPGRADES}/{upgrade_id}", profile=profile)


def get_upgrade_or_none(opts, upgrade_id, profile=None):
    try:
        return get_upgrade(opts, upgrade_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def start_upgrade(opts, upgrade_spec, profile=None):
    """Submit an upgrade request.

    *upgrade_spec* shape (per VCFA LCM):
    ``{"productId": "...", "targetVersion": "...", "options": {...}}``.
    Returns the upgrade record (with ``id``, ``state``).
    """
    return vcfa.api_post(opts, _UPGRADES, body=upgrade_spec, profile=profile)


def _upgrade_action(opts, upgrade_id, action, profile=None):
    return vcfa.api_post(
        opts, f"{_UPGRADES}/{upgrade_id}/actions", body={"action": action}, profile=profile
    )


def cancel_upgrade(opts, upgrade_id, profile=None):
    return _upgrade_action(opts, upgrade_id, "CANCEL", profile=profile)


def retry_upgrade(opts, upgrade_id, profile=None):
    return _upgrade_action(opts, upgrade_id, "RETRY", profile=profile)


def resume_upgrade(opts, upgrade_id, profile=None):
    return _upgrade_action(opts, upgrade_id, "RESUME", profile=profile)


def wait_for_upgrade(opts, upgrade_id, *, timeout=7200, poll_interval=30, profile=None):
    """Block until an upgrade reaches a terminal state. Returns the final record.

    Raises ``TimeoutError`` if the upgrade doesn't finish within *timeout*
    seconds, or ``RuntimeError`` on terminal failure / cancellation.
    """
    deadline = time.monotonic() + float(timeout)
    while True:
        rec = get_upgrade(opts, upgrade_id, profile=profile)
        state = (rec.get("state") or rec.get("status") or "").upper()
        if state in _TERMINAL_OK:
            return rec
        if state in _TERMINAL_BAD:
            raise RuntimeError(f"upgrade {upgrade_id!r} terminal failure: {state}")
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"upgrade {upgrade_id!r} did not finish within {timeout}s (last state: {state!r})"
            )
        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


def list_snapshots(opts, profile=None):
    resp = vcfa.api_get(opts, _SNAPSHOTS, profile=profile)
    return resp.get("content", []) or resp.get("items", []) or []


def get_snapshot(opts, snapshot_id, profile=None):
    return vcfa.api_get(opts, f"{_SNAPSHOTS}/{snapshot_id}", profile=profile)


def get_snapshot_or_none(opts, snapshot_id, profile=None):
    try:
        return get_snapshot(opts, snapshot_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_snapshot(opts, snapshot_spec, profile=None):
    """Take a system snapshot.

    *snapshot_spec* keys: ``name``, ``description``, ``includeData``
    (bool).
    """
    return vcfa.api_post(opts, _SNAPSHOTS, body=snapshot_spec, profile=profile)


def delete_snapshot(opts, snapshot_id, profile=None):
    return vcfa.api_delete(opts, f"{_SNAPSHOTS}/{snapshot_id}", profile=profile)


def restore_snapshot(opts, snapshot_id, profile=None):
    """Restore the system to *snapshot_id*. Returns the restore record."""
    return vcfa.api_post(opts, f"{_SNAPSHOTS}/{snapshot_id}/restore", body={}, profile=profile)


# ---------------------------------------------------------------------------
# Patches (baseline management)
# ---------------------------------------------------------------------------


_INSTALLED_STATES = {"INSTALLED", "APPLIED", "ACTIVE", "CURRENT"}
_AVAILABLE_STATES = {"AVAILABLE", "DOWNLOADED", "STAGED", "READY", "PENDING"}


def _unwrap_collection(resp):
    """Return the entries list from a VCFA response envelope.

    LCM responses come in one of three shapes depending on version:
    ``{"content": [...]}``, ``{"items": [...]}``, or a bare list. Also
    accepts ``{"patches": [...]}`` which some builds use for the patches
    sub-collection specifically.
    """
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        for key in ("content", "items", "patches", "results"):
            value = resp.get(key)
            if isinstance(value, list):
                return value
    return []


def list_patches(opts, product_id, profile=None):
    """List *all* patches known for *product_id* (installed + available).

    Prefers the dedicated ``/patches`` sub-collection; on 404 falls back
    to :func:`list_versions` filtered for entries whose ``kind`` /
    ``type`` marks them as a patch (as opposed to a full-version
    upgrade). Returns raw records — status classification is up to the
    caller / :func:`installed_patches` / :func:`available_patches`.
    """
    try:
        resp = vcfa.api_get(opts, f"{_PRODUCTS}/{product_id}/patches", profile=profile)
        entries = _unwrap_collection(resp)
        if entries:
            return entries
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 404:
            raise
    # Fallback: list_versions() and filter for patch-kind entries.
    versions = list_versions(opts, product_id, profile=profile)
    filtered = []
    for entry in versions:
        if not isinstance(entry, dict):
            continue
        kind = str(
            entry.get("kind") or entry.get("type") or entry.get("versionType") or ""
        ).upper()
        if kind in ("", "PATCH", "HOTFIX", "SP", "SERVICE_PACK"):
            filtered.append(entry)
    return filtered or versions


def _patch_status(entry):
    for key in ("status", "state", "installStatus", "installState"):
        value = entry.get(key)
        if value:
            return str(value).upper()
    if entry.get("installed") is True:
        return "INSTALLED"
    return ""


def installed_patches(opts, product_id, profile=None):
    """List patches currently applied to *product_id*.

    Filters :func:`list_patches` down to entries whose status is in
    :data:`_INSTALLED_STATES`.
    """
    return [
        entry
        for entry in list_patches(opts, product_id, profile=profile)
        if _patch_status(entry) in _INSTALLED_STATES
    ]


def available_patches(opts, product_id, profile=None):
    """List patches available for *product_id* but not yet installed."""
    return [
        entry
        for entry in list_patches(opts, product_id, profile=profile)
        if _patch_status(entry) in _AVAILABLE_STATES
    ]


def _patch_version_fields(entry):
    """Return every version-like string on *entry* (deduped, in preference order)."""
    if not isinstance(entry, dict):
        return []
    keys = ("version", "patchVersion", "name", "id", "displayVersion", "buildNumber", "build")
    seen = []
    for key in keys:
        val = entry.get(key)
        if val is None:
            continue
        s = str(val)
        if s and s not in seen:
            seen.append(s)
    return seen


def resolve_patch_version(entry):
    """Return the best "version" string for *entry*, or ``None`` if unresolvable."""
    fields = _patch_version_fields(entry)
    return fields[0] if fields else None


def find_patch(opts, product_id, version, profile=None):
    """Return the patch entry whose version matches *version*, or ``None``.

    Matches exact-then-prefix (either direction) across every
    version-like field on the entry — VCFA patch strings are
    inconsistent (dotted, dashed, build-numbered).
    """
    version = str(version)
    entries = list_patches(opts, product_id, profile=profile)
    for entry in entries:
        if version in _patch_version_fields(entry):
            return entry
    for entry in entries:
        for candidate in _patch_version_fields(entry):
            if candidate.startswith(version) or version.startswith(candidate):
                return entry
    return None


def is_patch_allowed(entry, allowed_versions):
    """True if *entry* matches any string in *allowed_versions*.

    Compares each allowed string against every version-like field on
    the entry using the same exact-then-prefix rule as
    :func:`find_patch`.
    """
    if entry is None or not allowed_versions:
        return False
    fields = _patch_version_fields(entry)
    if not fields:
        return False
    for allowed in allowed_versions:
        allowed = str(allowed)
        if allowed in fields:
            return True
        for candidate in fields:
            if candidate.startswith(allowed) or allowed.startswith(candidate):
                return True
    return False


def installed_patch_versions(opts, product_id, profile=None):
    """Convenience: return the resolved version strings of every installed patch."""
    return [
        resolve_patch_version(entry)
        for entry in installed_patches(opts, product_id, profile=profile)
        if resolve_patch_version(entry) is not None
    ]


def stage_patch(opts, product_id, version, profile=None):
    """Ask LCM to stage (download) *version* for *product_id*.

    Uses the upgrades collection with an explicit ``action=STAGE`` — the
    same submission shape :func:`apply_patch` uses, differing only in
    the action. Returns the upgrade record.
    """
    return vcfa.api_post(
        opts,
        _UPGRADES,
        body={"productId": product_id, "targetVersion": str(version), "action": "STAGE"},
        profile=profile,
    )


def apply_patch(opts, product_id, version, options=None, profile=None):
    """Submit a patch-install upgrade for *product_id* → *version*.

    Thin wrapper over :func:`start_upgrade` with the patch-specific
    action tag. *options* is merged into the request body verbatim.
    """
    body = {"productId": product_id, "targetVersion": str(version), "action": "APPLY_PATCH"}
    if options:
        body["options"] = options
    return start_upgrade(opts, body, profile=profile)
