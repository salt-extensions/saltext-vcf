"""NSX Management API — node services (``/api/v1/node/services/*``).

Currently wraps the HTTP service (``/node/services/http``) whose
``service_properties`` block controls DoS-mitigation knobs required by
STIG 912 controls:

- ``client_api_rate_limit`` — max requests/sec per client
- ``client_api_concurrency_limit`` — max concurrent requests per client
- ``global_api_concurrency_limit`` — max concurrent requests overall
- ``connection_timeout`` — idle connection timeout (seconds)
- ``redirect_host`` — hostname the manager redirects HTTP → HTTPS to

The endpoint is a singleton: PUT is a **total replacement** of the
config, so callers that only want to change a subset of fields must
read the current config, merge, and PUT the merged blob.
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
    """
    fields = {k: v for k, v in fields.items() if v is not None}
    current = http_get(opts, profile=profile)
    merged = dict(current) if isinstance(current, dict) else {}
    props = dict(merged.get("service_properties") or {})
    props.update(fields)
    merged["service_properties"] = props
    return http_put(opts, merged, profile=profile)
