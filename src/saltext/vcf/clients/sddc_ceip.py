"""SDDC Manager Customer Experience Improvement Program (CEIP) control.

On VCF 9.x the CEIP opt-in/opt-out is *SDDC-Manager-owned*, not a
per-appliance vCenter setting. SDDC Manager orchestrates the toggle
across every managed component (vCenter, ESXi hosts, NSX) via the task
subsystem; a naked ``PUT /api/appliance/ceip`` on the vCenter appliance
does not exist on this build (see ``docs/`` or the metamodel probe in
the fix-up PR for the empirical evidence).

The endpoint is::

    GET   /v1/system/ceip -> {"status": "ENABLED"|"DISABLED"|
                              "ENABLING"|"DISABLING"|
                              "ENABLING_FAILED"|"DISABLING_FAILED",
                              "instanceId": "<uuid>"}
    PATCH /v1/system/ceip {"status": "ENABLE" | "DISABLE"} -> 202 + task body

Note the verb mismatch: reads report present-tense state
(``ENABLED``/``DISABLED``/``DISABLING``), writes take the imperative
(``ENABLE``/``DISABLE``).
"""

from saltext.vcf.utils import sddc

PATH = "/v1/system/ceip"

# Present-tense states returned by GET
STATE_ENABLED = "ENABLED"
STATE_DISABLED = "DISABLED"
STATE_ENABLING = "ENABLING"
STATE_DISABLING = "DISABLING"
STATE_ENABLING_FAILED = "ENABLING_FAILED"
STATE_DISABLING_FAILED = "DISABLING_FAILED"

TERMINAL_STATES = {
    STATE_ENABLED,
    STATE_DISABLED,
    STATE_ENABLING_FAILED,
    STATE_DISABLING_FAILED,
}


def get(opts, profile=None):
    """Return the raw CEIP body: ``{"status": ..., "instanceId": ...}``."""
    return sddc.api_get(opts, PATH, profile=profile)


def status(opts, profile=None):
    """Return just the CEIP ``status`` string (present-tense)."""
    body = get(opts, profile=profile) or {}
    return body.get("status")


def is_enabled(opts, profile=None):
    """True when CEIP is fully ENABLED. In-flight or failed states report False."""
    return status(opts, profile=profile) == STATE_ENABLED


def set_(opts, enabled, profile=None):
    """PATCH the CEIP status. Async: returns the task body (``{"id": ..., "status": "IN_PROGRESS"}``).

    *enabled* is a boolean; True sends ``ENABLE``, False sends ``DISABLE``.
    """
    verb = "ENABLE" if bool(enabled) else "DISABLE"
    return sddc.api_patch(opts, PATH, body={"status": verb}, profile=profile)


def enable(opts, profile=None):
    """Convenience wrapper: opt-in to CEIP. Returns the task body."""
    return set_(opts, True, profile=profile)


def disable(opts, profile=None):
    """Convenience wrapper: opt-out of CEIP. Returns the task body."""
    return set_(opts, False, profile=profile)
