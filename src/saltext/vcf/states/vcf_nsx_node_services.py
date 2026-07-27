"""State module for NSX Manager node services.

Ships two verbs, both against ``/api/v1/node/services/{name}``:

- :func:`http_configured` — enforces DoS-mitigation ``service_properties``
  fields on ``/node/services/http`` (STIG 912 rate limits).

- :func:`logging_level_configured` — enforces
  ``service_properties.logging_level`` on any of the audit-logging
  services (``async_replicator``, ``http``, ``manager``, ``policy``)
  — the API equivalent of ``set service <name> logging-level <level>``.

.. code-block:: yaml

    nsx-http-rate-limits:
      vcf_nsx_node_services.http_configured:
        - client_api_rate_limit: 100
        - client_api_concurrency_limit: 40
        - global_api_concurrency_limit: 199

    nsx-audit-logging-manager:
      vcf_nsx_node_services.logging_level_configured:
        - service: manager
        - level: INFO

Each endpoint is a singleton with total-replacement PUT semantics; the
states read the current config, diff only the caller-supplied fields,
and PUT the merged document so unrelated fields (``redirect_host``,
``connection_timeout``, cipher config, …) are preserved.
"""

from saltext.vcf.clients import nsx_node_services as c

__virtualname__ = "vcf_nsx_node_services"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def http_configured(
    name,
    client_api_rate_limit=None,
    client_api_concurrency_limit=None,
    global_api_concurrency_limit=None,
    connection_timeout=None,
    redirect_host=None,
    profile=None,
    **extra,
):
    """Ensure the NSX HTTP service ``service_properties`` match the supplied fields.

    Only the fields the caller passes are considered; ``None`` means
    "don't touch". Fields already at the desired value are a no-op. If
    any field differs, the state reads the full current config, overlays
    the desired fields, and PUTs the merged document (the endpoint is
    total-replacement).
    """
    ret = _ret(name)

    desired = dict(extra)
    if client_api_rate_limit is not None:
        desired["client_api_rate_limit"] = client_api_rate_limit
    if client_api_concurrency_limit is not None:
        desired["client_api_concurrency_limit"] = client_api_concurrency_limit
    if global_api_concurrency_limit is not None:
        desired["global_api_concurrency_limit"] = global_api_concurrency_limit
    if connection_timeout is not None:
        desired["connection_timeout"] = connection_timeout
    if redirect_host is not None:
        desired["redirect_host"] = redirect_host

    if not desired:
        ret["comment"] = "No HTTP service fields supplied; nothing to do"
        return ret

    current = c.http_get(__opts__, profile=profile) or {}
    current_props = (current.get("service_properties") or {}) if isinstance(current, dict) else {}

    diffs = {}
    for key, want in desired.items():
        have = current_props.get(key)
        if have != want:
            diffs[key] = {"old": have, "new": want}

    if not diffs:
        ret["comment"] = "NSX HTTP service already matches desired fields"
        return ret

    if __opts__.get("test"):
        ret["result"] = None
        ret["changes"] = diffs
        ret["comment"] = f"NSX HTTP service would be updated: {sorted(diffs)}"
        return ret

    # Merge desired fields on top of the current config and PUT the whole
    # document. The endpoint is a singleton with total-replacement PUT
    # semantics — merging first is what keeps unrelated fields intact.
    merged = dict(current)
    merged_props = dict(current_props)
    merged_props.update(desired)
    merged["service_properties"] = merged_props
    c.http_put(__opts__, merged, profile=profile)

    ret["changes"] = diffs
    ret["comment"] = f"NSX HTTP service updated: {sorted(diffs)}"
    return ret


# Services on ``/api/v1/node/services/{name}`` known to expose
# ``service_properties.logging_level``. The state accepts any string —
# NSX rejects unknown service names with 404 — but this tuple is the
# authoritative STIG-912 set.
_LOGGING_SERVICES = ("async_replicator", "http", "manager", "policy")

# Levels NSX documents for ``logging_level``. Values are normalised to
# uppercase before comparison, matching what the manager returns.
_LOGGING_LEVELS = ("INFO", "WARNING", "ERROR", "DEBUG", "TRACE", "FATAL", "OFF")


def logging_level_configured(name, service, level, profile=None):
    """Ensure ``service_properties.logging_level`` on *service* equals *level*.

    Idempotent read-modify-write against
    ``/api/v1/node/services/{service}``: if the current
    ``logging_level`` already matches (case-insensitively) this is a
    no-op; otherwise the state merges the new level onto the current
    document and PUTs it back so unrelated ``service_properties`` are
    preserved.

    *service* must be one of ``async_replicator``, ``http``, ``manager``
    or ``policy`` — the four services whose CLI equivalent is
    ``set service <name> logging-level <level>``.
    """
    ret = _ret(name)

    if service not in _LOGGING_SERVICES:
        ret["result"] = False
        ret["comment"] = (
            f"Unknown NSX node service {service!r}; "
            f"expected one of {list(_LOGGING_SERVICES)}"
        )
        return ret

    desired = str(level).upper()
    if desired not in _LOGGING_LEVELS:
        ret["result"] = False
        ret["comment"] = (
            f"Unsupported logging level {level!r}; "
            f"expected one of {list(_LOGGING_LEVELS)}"
        )
        return ret

    current = c.service_get(__opts__, service, profile=profile) or {}
    current_props = (current.get("service_properties") or {}) if isinstance(current, dict) else {}
    have_raw = current_props.get("logging_level")
    have = str(have_raw).upper() if have_raw is not None else None

    if have == desired:
        ret["comment"] = f"NSX {service} logging_level already {desired}"
        return ret

    diffs = {"logging_level": {"old": have_raw, "new": desired}}

    if __opts__.get("test"):
        ret["result"] = None
        ret["changes"] = diffs
        ret["comment"] = f"NSX {service} logging_level would be set to {desired}"
        return ret

    merged = dict(current)
    merged_props = dict(current_props)
    merged_props["logging_level"] = desired
    merged["service_properties"] = merged_props
    c.service_put(__opts__, service, merged, profile=profile)

    ret["changes"] = diffs
    ret["comment"] = f"NSX {service} logging_level set to {desired}"
    return ret
