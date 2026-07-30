"""VCF Operations for Logs (vRLI) — Active Directory integration.

vRLI exposes AD configuration at ``/api/v2/ad``. Verbs discovered
live::

    GET  /api/v2/ad    -> {"enableAD": bool, ...}
    POST /api/v2/ad    body (all required):
                       {
                         "enableAD": bool,
                         "domain":   "corp.example.com",
                         "username": "svc-vrli",
                         "password": "...",
                         "connType": "STANDARD" | "GLOBAL_CAT" | "CUSTOM"
                       }

    PUT   /api/v2/ad   -> 404 "Handler not found"
    PATCH /api/v2/ad   -> 404 "Handler not found"

The 400 response body enumerates the exact required fields — this is
authoritative for the schema.
"""

from saltext.vcf.utils import vrli

_AD = "/api/v2/ad"

VALID_CONN_TYPES = ("STANDARD", "GLOBAL_CAT", "CUSTOM")


def get(opts, profile=None):
    """Return the current AD configuration.

    On a fresh appliance this is ``{"enableAD": false}``; once
    configured the returned dict includes ``domain``, ``username``,
    ``connType`` (password is never returned).
    """
    return vrli.api_get(opts, _AD, profile=profile)


def set_(opts, spec, profile=None):
    """Apply an AD configuration.

    *spec* is passed through to ``POST /api/v2/ad`` as-is. When
    ``enableAD`` is true, ``domain``, ``username``, ``password`` and
    ``connType`` are all required by the server. On success the
    endpoint returns an empty body (HTTP 200).
    """
    conn_type = spec.get("connType")
    if spec.get("enableAD") and conn_type not in VALID_CONN_TYPES:
        raise ValueError(f"connType must be one of {VALID_CONN_TYPES}, got {conn_type!r}")
    return vrli.api_post(opts, _AD, body=spec, profile=profile)


def disable(opts, profile=None):
    """Convenience wrapper — POST ``{"enableAD": false}``."""
    return vrli.api_post(opts, _AD, body={"enableAD": False}, profile=profile)
