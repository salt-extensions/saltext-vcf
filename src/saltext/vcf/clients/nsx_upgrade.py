"""NSX upgrade workflow (``/api/v1/upgrade/...``).

NSX-T's upgrade surface is two-layered: an *upgrade plan* drives an
ordered set of *upgrade unit groups* (host, edge, manager), each
containing the actual *upgrade units* (the hosts / edges / managers
being upgraded). Bundles supply the bits.

Endpoints used here (all NSX manager HTTP basic auth, via
:mod:`saltext.vcf.utils.nsx`):

* ``GET    /api/v1/upgrade/status-summary``         — overall progress + state
* ``GET    /api/v1/upgrade/upgrade-unit-groups``    — list groups
* ``GET    /api/v1/upgrade/upgrade-unit-groups/{id}``
* ``POST   /api/v1/upgrade/upgrade-unit-groups``    — create custom group
* ``PUT    /api/v1/upgrade/upgrade-unit-groups/{id}``
* ``DELETE /api/v1/upgrade/upgrade-unit-groups/{id}``
* ``GET    /api/v1/upgrade/upgrade-units``          — list units across groups
* ``GET    /api/v1/upgrade/upgrade-units/{id}``
* ``POST   /api/v1/upgrade/plan?action={start,pause,resume,reset}``
* ``GET    /api/v1/upgrade/plan/settings``          — current plan settings
* ``PUT    /api/v1/upgrade/plan/settings``          — update plan settings
* ``GET    /api/v1/upgrade/upgrade-bundles``        — uploaded bundles
* ``GET    /api/v1/upgrade/upgrade-bundles/{id}``
* ``POST   /api/v1/upgrade/upgrade-bundles?action=upload`` (multipart) — uploaded out-of-band today
* ``GET    /api/v1/upgrade/history``                — previous runs

The bundle upload itself is multipart and isn't wrapped here — drop a
bundle in via the NSX UI or the standalone ``curl`` recipe; this
client manages the workflow once a bundle is present.
"""

import time

import requests

from saltext.vcf.utils import nsx

_BASE = "/api/v1/upgrade"
_STATUS = f"{_BASE}/status-summary"
_PLAN = f"{_BASE}/plan"
_PLAN_SETTINGS = f"{_PLAN}/settings"
_GROUPS = f"{_BASE}/upgrade-unit-groups"
_UNITS = f"{_BASE}/upgrade-units"
_BUNDLES = f"{_BASE}/upgrade-bundles"
_HISTORY = f"{_BASE}/history"

# Terminal NSX overall_upgrade_status values. NSX historically uses both
# ``SUCCESS`` and ``COMPLETED`` depending on the version path; tolerate
# both.
_TERMINAL_OK = {"SUCCESS", "COMPLETED"}
_TERMINAL_BAD = {"FAILED", "PAUSED_DUE_TO_FAILURE"}


# ---------------------------------------------------------------------------
# Status + history
# ---------------------------------------------------------------------------


def status_summary(opts, profile=None):
    """Return the overall upgrade status (state, progress %, etc.)."""
    return nsx.api_get(opts, _STATUS, profile=profile)


def history(opts, profile=None):
    """Return the list of previous upgrade runs."""
    return nsx.api_get(opts, _HISTORY, profile=profile)


# ---------------------------------------------------------------------------
# Plan controls
# ---------------------------------------------------------------------------


def _plan_action(opts, action, profile=None):
    return nsx.api_post(opts, _PLAN, params={"action": action}, body={}, profile=profile)


def start(opts, profile=None):
    """Start the upgrade plan."""
    return _plan_action(opts, "start", profile=profile)


def pause(opts, profile=None):
    """Pause the upgrade plan."""
    return _plan_action(opts, "pause", profile=profile)


def resume(opts, profile=None):
    """Resume a paused plan."""
    return _plan_action(opts, "resume", profile=profile)


def reset(opts, profile=None):
    """Reset the plan back to initial state (discards group ordering)."""
    return _plan_action(opts, "reset", profile=profile)


def get_plan_settings(opts, profile=None):
    """Return the plan-level settings (parallelism, pre-checks, etc.)."""
    return nsx.api_get(opts, _PLAN_SETTINGS, profile=profile)


def update_plan_settings(opts, settings, profile=None):
    """Replace the plan-level settings document."""
    return nsx.api_put(opts, _PLAN_SETTINGS, body=settings, profile=profile)


# ---------------------------------------------------------------------------
# Upgrade unit groups
# ---------------------------------------------------------------------------


def list_groups(opts, profile=None):
    return nsx.api_get(opts, _GROUPS, profile=profile)


def get_group(opts, group_id, profile=None):
    return nsx.api_get(opts, f"{_GROUPS}/{group_id}", profile=profile)


def get_group_or_none(opts, group_id, profile=None):
    try:
        return get_group(opts, group_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_group(opts, group_spec, profile=None):
    """Create a custom upgrade unit group.

    *group_spec* keys: ``display_name``, ``type``
    (``HOST``/``EDGE``/``MP``), ``upgrade_units`` (list of unit refs),
    ``enabled``, ``parallel``, ``extended_configuration``.
    """
    return nsx.api_post(opts, _GROUPS, body=group_spec, profile=profile)


def update_group(opts, group_id, group_spec, profile=None):
    return nsx.api_put(opts, f"{_GROUPS}/{group_id}", body=group_spec, profile=profile)


def delete_group(opts, group_id, profile=None):
    return nsx.api_delete(opts, f"{_GROUPS}/{group_id}", profile=profile)


# ---------------------------------------------------------------------------
# Upgrade units
# ---------------------------------------------------------------------------


def list_units(opts, group_id=None, profile=None):
    params = {"upgrade_unit_group_id": group_id} if group_id else None
    return nsx.api_get(opts, _UNITS, params=params, profile=profile)


def get_unit(opts, unit_id, profile=None):
    return nsx.api_get(opts, f"{_UNITS}/{unit_id}", profile=profile)


def get_unit_or_none(opts, unit_id, profile=None):
    try:
        return get_unit(opts, unit_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


# ---------------------------------------------------------------------------
# Bundles (read-only here)
# ---------------------------------------------------------------------------


def list_bundles(opts, profile=None):
    return nsx.api_get(opts, _BUNDLES, profile=profile)


def get_bundle(opts, bundle_id, profile=None):
    return nsx.api_get(opts, f"{_BUNDLES}/{bundle_id}", profile=profile)


def get_bundle_or_none(opts, bundle_id, profile=None):
    try:
        return get_bundle(opts, bundle_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


# ---------------------------------------------------------------------------
# Waiter
# ---------------------------------------------------------------------------


def wait_for_completion(opts, *, timeout=14400, poll_interval=30, profile=None):
    """Block until ``status-summary`` reports a terminal state.

    Returns the final ``status-summary`` body. Raises ``TimeoutError``
    if no terminal state in *timeout* seconds, or ``RuntimeError`` on
    terminal failure / paused-due-to-failure.
    """
    deadline = time.monotonic() + float(timeout)
    while True:
        summary = status_summary(opts, profile=profile)
        state = (summary.get("overall_upgrade_status") or summary.get("status") or "").upper()
        if state in _TERMINAL_OK:
            return summary
        if state in _TERMINAL_BAD:
            raise RuntimeError(f"NSX upgrade terminal failure: {state}")
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"NSX upgrade did not finish within {timeout}s (last state: {state!r})"
            )
        time.sleep(poll_interval)
