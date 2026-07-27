"""NSX Management API — node services (``/api/v1/node/services/*``).

Wraps the per-service configuration endpoints exposed under
``/api/v1/node/services/{service_name}``. Each endpoint is a singleton
whose ``service_properties`` block carries per-service knobs.

Two families of controls this module supports today:

- **HTTP service** (``/node/services/http``) — DoS-mitigation knobs
  required by STIG 912 controls:

  - ``client_api_rate_limit`` — max requests/sec per client
  - ``client_api_concurrency_limit`` — max concurrent requests per client
  - ``global_api_concurrency_limit`` — max concurrent requests overall
  - ``connection_timeout`` — idle connection timeout (seconds)
  - ``redirect_host`` — hostname the manager redirects HTTP → HTTPS to

- **Audit-logging services** (``manager``, ``policy``,
  ``async_replicator``, ``http``) — ``service_properties.logging_level``
  (``INFO`` / ``WARNING`` / ``ERROR`` / ``DEBUG`` / ``TRACE``).
  Manager-CLI equivalent: ``set service <service> logging-level <level>``.

Every ``PUT`` on these endpoints is a **total replacement** of the
config, so the ``_set`` helpers do a read-modify-write, merging the
caller's fields on top of the current document and PUTting the whole
blob.
"""

from saltext.vcf.utils import nsx

HTTP_PATH = "/api/v1/node/services/http"

# Services that expose ``service_properties.logging_level`` on
# ``/api/v1/node/services/{name}``. Kept here as documentation; the
# generic helpers accept any service name NSX serves.
LOGGING_SERVICES = ("async_replicator", "http", "manager", "policy")


def _service_path(service_name):
    return f"/api/v1/node/services/{service_name}"


def service_get(opts, service_name, profile=None):
    """Return the config document for ``/api/v1/node/services/{service_name}``."""
    return nsx.api_get(opts, _service_path(service_name), profile=profile)


def service_put(opts, service_name, body, profile=None):
    """PUT a complete service configuration blob to NSX.

    *body* is the entire node-services document for *service_name* — the
    endpoint does NOT accept partial updates. Callers wanting to change
    only certain ``service_properties`` fields should use
    :func:`service_set`, which read-merge-PUTs.
    """
    return nsx.api_put(opts, _service_path(service_name), body=body, profile=profile)


def service_set(opts, service_name, profile=None, **fields):
    """Update *fields* under ``service_properties`` idempotently.

    Reads the current config for *service_name*, overlays the supplied
    ``service_properties`` fields, and PUTs the merged document back.
    Returns the PUT response.

    Any ``fields`` key that is ``None`` is dropped (treated as
    "leave as-is").
    """
    fields = {k: v for k, v in fields.items() if v is not None}
    current = service_get(opts, service_name, profile=profile)
    merged = dict(current) if isinstance(current, dict) else {}
    props = dict(merged.get("service_properties") or {})
    props.update(fields)
    merged["service_properties"] = props
    return service_put(opts, service_name, merged, profile=profile)


# ---------------------------------------------------------------------------
# HTTP service convenience wrappers (original STIG-912 rate-limit surface).
# ---------------------------------------------------------------------------


def http_get(opts, profile=None):
    """Return the current NSX Manager HTTP service configuration."""
    return service_get(opts, "http", profile=profile)


def http_put(opts, body, profile=None):
    """PUT a complete HTTP service configuration blob to NSX."""
    return service_put(opts, "http", body, profile=profile)


def http_set(opts, profile=None, **fields):
    """Update *fields* under HTTP ``service_properties`` idempotently."""
    return service_set(opts, "http", profile=profile, **fields)


# ---------------------------------------------------------------------------
# Audit-logging convenience wrappers (manager / policy / async_replicator).
# The HTTP service also carries a ``logging_level``; use ``http_set`` for it.
# ---------------------------------------------------------------------------


def manager_get(opts, profile=None):
    """Return the NSX ``manager`` service configuration."""
    return service_get(opts, "manager", profile=profile)


def manager_set(opts, profile=None, **fields):
    """Update ``manager`` ``service_properties`` idempotently."""
    return service_set(opts, "manager", profile=profile, **fields)


def policy_get(opts, profile=None):
    """Return the NSX ``policy`` service configuration."""
    return service_get(opts, "policy", profile=profile)


def policy_set(opts, profile=None, **fields):
    """Update ``policy`` ``service_properties`` idempotently."""
    return service_set(opts, "policy", profile=profile, **fields)


def async_replicator_get(opts, profile=None):
    """Return the NSX ``async_replicator`` service configuration."""
    return service_get(opts, "async_replicator", profile=profile)


def async_replicator_set(opts, profile=None, **fields):
    """Update ``async_replicator`` ``service_properties`` idempotently."""
    return service_set(opts, "async_replicator", profile=profile, **fields)
