"""NSX Management API — node services (``/api/v1/node/services/*``).

Currently wraps the HTTP service (``/node/services/http``) whose
``service_properties`` block controls DoS-mitigation and TLS knobs
required by STIG 912 controls:

- ``client_api_rate_limit`` — max requests/sec per client
- ``client_api_concurrency_limit`` — max concurrent requests per client
- ``global_api_concurrency_limit`` — max concurrent requests overall
- ``connection_timeout`` — idle connection timeout (seconds)
- ``redirect_host`` — hostname the manager redirects HTTP → HTTPS to
- ``cipher_suites`` — list of enabled TLS cipher suites (each a
  ``{"enabled": bool, "name": <suite>}`` dict per NSX schema, or a
  bare suite name — the caller decides what NSX accepts on this build).
  Used to satisfy the ISA "Encryption Requirements / Enable TLS 1.2"
  control that requires unapproved cipher suites be disabled.
- ``protocols`` — list of enabled TLS protocol versions, typically
  ``[{"enabled": True, "name": "TLSv1_2"}, ...]`` or the bare-string
  variant depending on NSX build. STIG requires TLS 1.2 (or higher).

The endpoint is a singleton: PUT is a **total replacement** of the
config, so callers that only want to change a subset of fields must
read the current config, merge, and PUT the merged blob. Both
:func:`http_set` and :func:`http_tls_set` handle that read-merge-PUT
dance for you and accept ``cipher_suites`` / ``protocols`` as
keyword args.
"""

from saltext.vcf.utils import nsx

HTTP_PATH = "/api/v1/node/services/http"


def http_get(opts, profile=None):
    """Return the current NSX Manager HTTP service configuration."""
    return nsx.api_get(opts, HTTP_PATH, profile=profile)


def http_put(opts, body, profile=None):
    """PUT a complete HTTP service configuration blob to NSX.

    *body* is the entire node-services-http document — this endpoint does
    NOT accept partial updates. Callers that want to change only certain
    ``service_properties`` fields should ``http_get`` first, merge onto
    the returned document, and pass the result here.
    """
    return nsx.api_put(opts, HTTP_PATH, body=body, profile=profile)


def http_set(opts, profile=None, **fields):
    """Update *fields* under ``service_properties`` idempotently.

    Reads the current config, overlays the supplied ``service_properties``
    fields, and PUTs the merged document back. Returns the PUT response.

    Any ``fields`` key that is ``None`` is dropped (treated as "leave as-is").

    Accepts DoS-mitigation fields (``client_api_rate_limit``,
    ``client_api_concurrency_limit``, ``global_api_concurrency_limit``,
    ``connection_timeout``, ``redirect_host``) *and* the TLS fields
    (``cipher_suites``, ``protocols``) — kwargs are passed through
    verbatim onto ``service_properties``.
    """
    fields = {k: v for k, v in fields.items() if v is not None}
    current = http_get(opts, profile=profile)
    merged = dict(current) if isinstance(current, dict) else {}
    props = dict(merged.get("service_properties") or {})
    props.update(fields)
    merged["service_properties"] = props
    return http_put(opts, merged, profile=profile)


def http_tls_set(opts, protocols=None, cipher_suites=None, profile=None):
    """Set the HTTP service TLS ``protocols`` / ``cipher_suites`` idempotently.

    Convenience wrapper around :func:`http_set` restricted to the two
    TLS-relevant fields. Either argument may be ``None`` to leave that
    field untouched (useful for single-field updates). Read-merge-PUTs
    like :func:`http_set` so DoS-mitigation fields are preserved.

    STIG 912 / ISA Encryption Requirements: ``protocols`` should enable
    only TLSv1.2 and above; ``cipher_suites`` should enable only
    approved suites per the ISA Cryptographic Requirements doc.
    """
    return http_set(
        opts, profile=profile, protocols=protocols, cipher_suites=cipher_suites
    )
