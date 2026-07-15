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
* ``GET    /lcm/api/upgrades``                      — list upgrade requests
* ``GET    /lcm/api/upgrades/{upgradeId}``          — one upgrade request
* ``POST   /lcm/api/upgrades``                      — start an upgrade
* ``POST   /lcm/api/upgrades/{upgradeId}/actions``  — cancel / retry / resume
* ``GET    /lcm/api/snapshots``                     — list system snapshots
* ``GET    /lcm/api/snapshots/{snapshotId}``        — one snapshot
* ``POST   /lcm/api/snapshots``                     — create a snapshot
* ``DELETE /lcm/api/snapshots/{snapshotId}``        — delete a snapshot
* ``POST   /lcm/api/snapshots/{snapshotId}/restore``— restore a snapshot
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
