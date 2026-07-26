"""NSX Management API — telemetry / CEIP configuration (singleton).

The Customer Experience Improvement Program (CEIP) opt-in on NSX Manager is
managed via the classic Manager API under ``/api/v1/telemetry/config``. The
resource is a singleton (no id) and the ``ceip_acceptance`` boolean drives
whether the manager transmits usage data to Broadcom/VMware. Setting
``ceip_acceptance: false`` satisfies the 912 Controls requirement that "The
NSX-T Manager must not provide environment information to third parties."
"""

from saltext.vcf.utils import nsx

PATH = "/api/v1/telemetry/config"


def get(opts, profile=None):
    """Return the current NSX telemetry / CEIP configuration."""
    return nsx.api_get(opts, PATH, profile=profile)


def update(opts, profile=None, **body):
    """Replace the NSX telemetry configuration with *body* via PUT.

    Callers should include the full config document as returned by :func:`get`
    (with any fields modified) since the endpoint is a PUT-style replace.
    """
    return nsx.api_put(opts, PATH, body=body, profile=profile)


def set_ceip_acceptance(opts, ceip_acceptance, profile=None):
    """Set the CEIP ``ceip_acceptance`` flag, preserving other fields from the current config.

    Reads the current config, updates the ``ceip_acceptance`` key, and PUTs it
    back so other telemetry settings (schedule, proxy, etc.) are not clobbered.
    """
    current = get(opts, profile=profile) or {}
    body = dict(current)
    body["ceip_acceptance"] = bool(ceip_acceptance)
    return nsx.api_put(opts, PATH, body=body, profile=profile)
