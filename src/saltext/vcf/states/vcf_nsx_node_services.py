"""State module for NSX Manager node services.

Ships two verbs against ``/api/v1/node/services/http``:

* :func:`http_configured` — DoS-mitigation ``service_properties``
  (rate limits, connection timeout, redirect host) for STIG 912.
* :func:`tls_configured` — ``protocols`` / ``cipher_suites`` for the
  ISA "Encryption Requirements / Enable TLS 1.2" control (also
  STIG 912 series).

.. code-block:: yaml

    nsx-http-rate-limits:
      vcf_nsx_node_services.http_configured:
        - client_api_rate_limit: 100
        - client_api_concurrency_limit: 40
        - global_api_concurrency_limit: 199

    nsx-http-tls:
      vcf_nsx_node_services.tls_configured:
        - protocols:
            - TLSv1_2
            - TLSv1_3
        - cipher_suites:
            - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
            - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256

The endpoint is a singleton with total-replacement PUT semantics; both
states read the current config, diff only the caller-supplied fields,
and PUT the merged document so unrelated fields are preserved.
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


def tls_configured(name, protocols=None, cipher_suites=None, profile=None):
    """Ensure the NSX HTTP service TLS ``protocols`` / ``cipher_suites`` match.

    Only fields the caller supplies are considered; ``None`` means
    "leave alone". This state is idempotent on those two fields only —
    unrelated ``service_properties`` (rate limits, connection timeout,
    redirect host) are read-merged before PUT so they stay put.

    Satisfies the ISA "Encryption Requirements / Enable TLS 1.2"
    control: TLS 1.2+ must be enabled and unapproved cipher suites
    must be disabled for all encrypted communications.
    """
    ret = _ret(name)

    desired = {}
    if protocols is not None:
        desired["protocols"] = protocols
    if cipher_suites is not None:
        desired["cipher_suites"] = cipher_suites

    if not desired:
        ret["comment"] = "No TLS fields supplied; nothing to do"
        return ret

    current = c.http_get(__opts__, profile=profile) or {}
    current_props = (current.get("service_properties") or {}) if isinstance(current, dict) else {}

    diffs = {}
    for key, want in desired.items():
        have = current_props.get(key)
        if have != want:
            diffs[key] = {"old": have, "new": want}

    if not diffs:
        ret["comment"] = "NSX HTTP TLS config already matches desired fields"
        return ret

    if __opts__.get("test"):
        ret["result"] = None
        ret["changes"] = diffs
        ret["comment"] = f"NSX HTTP TLS config would be updated: {sorted(diffs)}"
        return ret

    # Read-merge-PUT: total-replacement endpoint, so we overlay onto the
    # current doc to keep DoS-mitigation fields (and any future fields
    # NSX adds) intact.
    merged = dict(current)
    merged_props = dict(current_props)
    merged_props.update(desired)
    merged["service_properties"] = merged_props
    c.http_put(__opts__, merged, profile=profile)

    ret["changes"] = diffs
    ret["comment"] = f"NSX HTTP TLS config updated: {sorted(diffs)}"
    return ret
