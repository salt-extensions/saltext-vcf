"""
Client for vCenter's VAMI appliance-update REST API (VCSA self-patching).

Manages the vCenter appliance's own update lifecycle — configuring an
update repository, listing/resolving pending updates, staging a build,
running prechecks, and installing — via::

    /rest/appliance/update/...

This is a distinct workflow from ESXi host patching
(:mod:`saltext.vcf.clients.esxi_vlcm`, vLCM) or NSX/SDDC Manager
component upgrades — it patches the vCenter Server Appliance itself.

Authentication reuses the same vCenter session as every other
``/api/...`` client in this package
(:mod:`saltext.vcf.utils.vcenter`): a ``vmware-api-session-id`` token
obtained via ``POST /api/session`` is also valid against the legacy
``/rest/...`` vSphere Automation API namespace used here — both
namespaces share the same underlying vAPI session on modern vCenter
builds, so no separate login is needed. If a target vCenter build
rejects that token for ``/rest/...`` calls, a read-only call like
:func:`get_update_policy` will fail fast with 401/403 — verify with one
before running anything mutating.
"""

import logging
import time
from urllib.parse import quote

import requests

from saltext.vcf.utils import vcenter

log = logging.getLogger(__name__)

_BASE = "/rest/appliance/update"

TRANSIENT_STATUS_CODES = (401, 403, 404, 500, 502, 503)
STAGE_TIMEOUT_MARKERS = ("Timeout happens while waiting for task out file", "task out file")
STAGING_IN_PROGRESS_MARKERS = ("Update staging is in progress", "precheck.not_allowed_error")


def _quoted(version):
    return quote(str(version), safe="")


def _error_text(exc):
    """Exception message plus the HTTP response body, when available.

    Some VAMI failure signatures (stage timeout, precheck-not-allowed) are
    only detectable by inspecting the response body text, not the bare
    exception message.
    """
    resp = getattr(exc, "response", None)
    if resp is not None:
        try:
            return f"{exc} {resp.text}"
        except Exception:  # pylint: disable=broad-except
            pass
    return str(exc)


def is_transient_error(exc):
    """True if *exc* is an HTTP error VAMI services commonly throw mid-patch.

    The appliance's own update services restart during staging/install,
    which can surface as 401/403/404/500/502/503 on the next poll — treated
    as transient (retry after re-authenticating), not a hard failure.
    """
    resp = getattr(exc, "response", None)
    return resp is not None and resp.status_code in TRANSIENT_STATUS_CODES


def is_stage_timeout_error(exc):
    """True if *exc* is VAMI's "stage still running server-side" signature.

    The REST call itself can time out client-side while staging continues
    on the appliance; callers should fall back to polling
    :func:`get_staged_update` instead of treating this as a hard failure.
    """
    return any(m in _error_text(exc) for m in STAGE_TIMEOUT_MARKERS)


def is_staging_in_progress_error(exc):
    """True if *exc* is VAMI refusing a precheck because staging isn't done yet."""
    return any(m in _error_text(exc) for m in STAGING_IN_PROGRESS_MARKERS)


# ---------------------------------------------------------------------------
# Repository policy
# ---------------------------------------------------------------------------


def get_update_policy(opts, profile=None):
    """Return the appliance's current update-repository policy."""
    return vcenter.api_get(opts, f"{_BASE}/policy", profile=profile)


def set_update_policy(
    opts,
    repository_url,
    auto_stage=False,
    certificate_check=True,
    check_schedule=None,
    repo_username="",
    repo_password="",
    profile=None,
):
    """Configure the appliance's update-repository policy.

    *repository_url* is required. All other fields are always sent with a
    real value (never omitted), matching the reference implementation this
    was ported from — every field of this action is meant to fully replace
    the prior policy, not merge into it.
    """
    body = {
        "policy": {
            "auto_stage": auto_stage,
            "check_schedule": check_schedule if check_schedule is not None else [],
            "certificate_check": certificate_check,
            "custom_URL": repository_url,
            "username": repo_username or "",
            "password": repo_password or "",
        }
    }
    return vcenter.api_put(opts, f"{_BASE}/policy", body=body, profile=profile)


# ---------------------------------------------------------------------------
# Pending updates
# ---------------------------------------------------------------------------


def list_pending_updates(opts, repository_url=None, source_type="LOCAL_AND_ONLINE", profile=None):
    """List updates available from the configured sources.

    *source_type* is forced to ``"LOCAL_AND_URL"`` whenever *repository_url*
    is given, regardless of what's passed in, matching VAMI's expectation
    that a URL-scoped lookup declares itself as such.
    """
    params = {
        "source_type": "LOCAL_AND_URL" if repository_url else source_type,
    }
    if repository_url:
        params["url"] = repository_url
    return vcenter.api_get(opts, f"{_BASE}/pending", params=params, profile=profile)


def get_pending_update(opts, version, profile=None):
    """Return details for one specific pending update *version*."""
    return vcenter.api_get(opts, f"{_BASE}/pending/{_quoted(version)}", profile=profile)


def list_upgradeable_components(opts, version, profile=None):
    """List the components that would be upgraded by *version*."""
    return vcenter.api_get(
        opts, f"{_BASE}/pending/{_quoted(version)}/components", profile=profile
    )


def get_update_status(opts, profile=None):
    """Return the appliance's overall update state machine status."""
    return vcenter.api_get(opts, _BASE, profile=profile)


def precheck(opts, version, component=None, profile=None):
    """Run pre-update health checks for *version*.

    No body is sent when *component* is omitted — a whole-appliance
    precheck doesn't take one.
    """
    return vcenter.api_post(
        opts,
        f"{_BASE}/pending/{_quoted(version)}",
        body={"component": component} if component else None,
        params={"action": "precheck"},
        profile=profile,
    )


def stage(opts, version, component=None, profile=None):
    """Download/stage the update payload for *version*. See :func:`precheck` on body."""
    return vcenter.api_post(
        opts,
        f"{_BASE}/pending/{_quoted(version)}",
        body={"component": component} if component else None,
        params={"action": "stage"},
        profile=profile,
    )


def install(opts, version, sso_password, component=None, profile=None):
    """Install the staged update for *version*.

    *sso_password* (the SSO admin/vmdir password) is required — VAMI needs
    it to re-authenticate vmdir during the appliance install.
    """
    body = {"user_data": [{"key": "vmdir.password", "value": sso_password}]}
    if component:
        body["component"] = component
    return vcenter.api_post(
        opts,
        f"{_BASE}/pending/{_quoted(version)}",
        body=body,
        params={"action": "install"},
        profile=profile,
    )


# ---------------------------------------------------------------------------
# Staged update
# ---------------------------------------------------------------------------


def _get_tolerant(opts, path, profile=None):
    """GET *path*, returning the parsed body (or ``{}``) instead of raising on 404."""
    try:
        return vcenter.api_get(opts, path, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            try:
                return exc.response.json()
            except ValueError:
                return {}
        raise


def get_staged_update(opts, profile=None):
    """Return the currently staged update, or an empty/error body if nothing is staged."""
    return _get_tolerant(opts, f"{_BASE}/staged", profile=profile)


def delete_staged_update(opts, profile=None):
    """Discard the currently staged update. Tolerant of "nothing staged" (404)."""
    try:
        return vcenter.api_delete(opts, f"{_BASE}/staged", profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return {}
        raise


def get_update_history(opts, profile=None):
    """Return the appliance's update history log."""
    return vcenter.api_get(opts, f"{_BASE}/history", profile=profile)


# ---------------------------------------------------------------------------
# staged/version matching
# ---------------------------------------------------------------------------


def staged_matches(staged_update, version=None):
    """True if *staged_update* (a :func:`get_staged_update` response) is non-empty.

    If *version* is given, also requires it to match the staged entry's
    version-like fields (exact, or a prefix match in either direction —
    VAMI's version strings mix build numbers/dotted versions/display
    names, so exact string equality is too strict).
    """
    if not staged_update:
        return False
    value = staged_update.get("value") if isinstance(staged_update, dict) else staged_update
    if value in (None, "", {}, []):
        return False
    if not version:
        return True
    version = str(version)
    candidates = []
    if isinstance(value, dict):
        candidates += [
            value.get("version"),
            value.get("name"),
            value.get("id"),
            value.get("display_version"),
        ]
        for key in ("update", "info", "summary"):
            nested = value.get(key)
            if isinstance(nested, dict):
                candidates += [
                    nested.get("version"),
                    nested.get("name"),
                    nested.get("id"),
                    nested.get("display_version"),
                ]
    elif isinstance(value, str):
        candidates.append(value)
    return any(
        str(c) == version or str(c).startswith(version) or version.startswith(str(c))
        for c in candidates
        if c
    )


def _extract_values(pending_updates):
    if isinstance(pending_updates, dict):
        value = pending_updates.get("value", [])
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return list(value.values())
    if isinstance(pending_updates, list):
        return pending_updates
    return []


def _version_fields(item):
    return [item.get("version"), item.get("name"), item.get("id"), item.get("display_version")]


def _match_version(values, requested):
    dict_values = [v for v in values if isinstance(v, dict)]
    for item in dict_values:
        if any(str(c) == requested for c in _version_fields(item) if c is not None):
            return item
    for item in dict_values:
        candidates = _version_fields(item)
        if any(
            str(c).startswith(requested) or requested.startswith(str(c))
            for c in candidates
            if c is not None
        ):
            return item
    return None


def resolve_update_version(opts, repository_url=None, version=None, profile=None):
    """Resolve a requested (or absent) *version* to a concrete pending-update version.

    If *version* is given, try a direct lookup first; on failure (or if
    omitted), list pending updates and match by exact-then-prefix on
    version/name/id/display_version. An absent *version* resolves to the
    first pending update returned by the server.

    Returns ``(resolved_version, pending_updates_raw, pending_update_detail)``.
    """
    pending_updates = None
    if version is not None and str(version).lower() not in ("", "none", "null"):
        try:
            pending_update = get_pending_update(opts, version, profile=profile)
            return str(version), pending_updates, pending_update
        except requests.HTTPError:
            pass

    pending_updates = list_pending_updates(opts, repository_url=repository_url, profile=profile)
    values = _extract_values(pending_updates)
    if not values:
        raise RuntimeError(
            f"No pending VCSA updates found. repository_url={repository_url!r}, "
            f"requested_version={version!r}"
        )

    if version is not None and str(version).lower() not in ("", "none", "null"):
        matched = _match_version(values, str(version))
        if not matched:
            available = [v.get("version") or v.get("name") for v in values if isinstance(v, dict)]
            raise RuntimeError(
                f"Requested VCSA update version {version!r} not found. Available: {available}"
            )
    else:
        matched = values[0]

    resolved = matched.get("version") or matched.get("name") or matched.get("id")
    if not resolved:
        raise RuntimeError(f"Unable to resolve VCSA update version from {matched}")
    try:
        pending_update = get_pending_update(opts, resolved, profile=profile)
    except requests.HTTPError:
        pending_update = matched
    return resolved, pending_updates, pending_update


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------


def _extract_state(status):
    if isinstance(status, dict):
        value = status.get("value")
        if isinstance(value, dict):
            return value.get("state")
        return status.get("state")
    return None


def wait_for_staged_update(opts, version=None, poll_interval=10, timeout=600, profile=None):
    """Block until :func:`get_staged_update` matches *version* (or anything staged, if omitted).

    Used as a fallback after a client-side timeout on :func:`stage` — the
    stage call may still be running server-side even though the REST
    response never came back in time.
    """
    deadline = time.time() + timeout
    last = None
    while True:
        try:
            staged = get_staged_update(opts, profile=profile)
            last = staged
            if staged_matches(staged, version):
                return {"success": True, "state": "STAGED", "staged_update": staged}
        except requests.HTTPError as exc:
            log.debug("staged update check failed: %s", exc)
        if time.time() > deadline:
            raise TimeoutError(f"Timed out waiting for staged update. Last response: {last}")
        time.sleep(poll_interval)


def monitor_stage(
    opts, version=None, poll_interval=50, timeout=3600, max_transient_errors=10, profile=None
):
    """Block until *version* is staged, or raise on failure/timeout.

    Tolerates transient HTTP errors (appliance services bouncing mid-patch)
    up to *max_transient_errors*, re-authenticating before each retry.
    """
    deadline = time.time() + timeout
    last_status = None
    last_state = None
    transient_errors = 0
    while True:
        try:
            staged = get_staged_update(opts, profile=profile)
            if staged_matches(staged, version):
                return {
                    "success": True,
                    "state": "STAGED",
                    "status": last_status,
                    "staged_update": staged,
                }
        except requests.HTTPError as exc:
            log.debug("unable to read staged update: %s", exc)
        try:
            status = get_update_status(opts, profile=profile)
            last_status = status
            transient_errors = 0
            state = _extract_state(status)
            if state != last_state:
                log.info("VCSA stage status=%s", state)
                last_state = state
            if state in ("STAGE_FAILED", "INSTALL_FAILED"):
                raise RuntimeError(f"VCSA stage failed. Status: {status}")
        except requests.HTTPError as exc:
            if not is_transient_error(exc):
                raise
            transient_errors += 1
            log.warning(
                "transient error while monitoring VCSA stage (%s/%s): %s",
                transient_errors,
                max_transient_errors,
                exc,
            )
            vcenter.invalidate_session(opts, profile=profile)
            if transient_errors >= max_transient_errors:
                raise RuntimeError(
                    f"VCSA stage monitor failed after {max_transient_errors} transient "
                    f"errors. Last error: {exc}"
                ) from exc
        if time.time() > deadline:
            raise TimeoutError(
                f"Timed out waiting for VCSA stage after {timeout}s. Last status: {last_status}"
            )
        time.sleep(poll_interval)


def monitor_install(opts, poll_interval=120, timeout=7200, max_transient_errors=10, profile=None):
    """Block until the appliance reports ``UP_TO_DATE``, or raise on failure/timeout."""
    deadline = time.time() + timeout
    last_status = None
    transient_errors = 0
    while True:
        try:
            status = get_update_status(opts, profile=profile)
            last_status = status
            transient_errors = 0
            state = _extract_state(status)
            log.info("VCSA install status=%s", state)
            if state == "UP_TO_DATE":
                return {"success": True, "state": state, "status": status}
            if state == "INSTALL_FAILED":
                raise RuntimeError(f"Install failed. Status: {status}")
        except requests.HTTPError as exc:
            if not is_transient_error(exc):
                raise
            transient_errors += 1
            log.warning(
                "transient error while monitoring VCSA install (%s/%s): %s",
                transient_errors,
                max_transient_errors,
                exc,
            )
            vcenter.invalidate_session(opts, profile=profile)
            if transient_errors >= max_transient_errors:
                raise RuntimeError(
                    f"VCSA install monitor failed after {max_transient_errors} transient "
                    f"errors. Last error: {exc}"
                ) from exc
        if time.time() > deadline:
            raise TimeoutError(f"Timed out waiting for install. Last status: {last_status}")
        time.sleep(poll_interval)
