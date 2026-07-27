"""State module for NSX Manager node services.

Currently ships one verb, :func:`http_configured`, which enforces
``service_properties`` fields on ``/api/v1/node/services/http``. This is
the surface used to satisfy STIG 912 DoS-mitigation controls:

.. code-block:: yaml

    nsx-http-rate-limits:
      vcf_nsx_node_services.http_configured:
        - client_api_rate_limit: 100
        - client_api_concurrency_limit: 40
        - global_api_concurrency_limit: 199

The endpoint is a singleton with total-replacement PUT semantics; the
state reads the current config, diffs only the caller-supplied fields,
and PUTs the merged document so unrelated fields (``redirect_host``,
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
