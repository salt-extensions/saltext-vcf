"""Execution module for NSX Management API — node services.

Thin wrapper over :mod:`saltext.vcf.clients.nsx_node_services`. Exposes the
HTTP service endpoint that carries the DoS-mitigation rate/concurrency
limits required by STIG 912.
"""

from saltext.vcf.clients import nsx_node_services as c

__virtualname__ = "vcf_nsx_node_services"


def __virtual__():
    return __virtualname__


def http_get(profile=None):
    """Return the NSX Manager HTTP service configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.http_get

    """
    return c.http_get(__opts__, profile=profile)


def http_set(
    client_api_rate_limit=None,
    client_api_concurrency_limit=None,
    global_api_concurrency_limit=None,
    connection_timeout=None,
    redirect_host=None,
    profile=None,
    **extra,
):
    """Merge the supplied ``service_properties`` fields into the NSX HTTP config.

    Any argument left as ``None`` is not written. The endpoint is a total
    replacement, so this reads → merges → PUTs to preserve unrelated fields.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.http_set \
            client_api_rate_limit=100 \
            client_api_concurrency_limit=40 \
            global_api_concurrency_limit=199

    """
    fields = dict(extra)
    if client_api_rate_limit is not None:
        fields["client_api_rate_limit"] = client_api_rate_limit
    if client_api_concurrency_limit is not None:
        fields["client_api_concurrency_limit"] = client_api_concurrency_limit
    if global_api_concurrency_limit is not None:
        fields["global_api_concurrency_limit"] = global_api_concurrency_limit
    if connection_timeout is not None:
        fields["connection_timeout"] = connection_timeout
    if redirect_host is not None:
        fields["redirect_host"] = redirect_host
    return c.http_set(__opts__, profile=profile, **fields)
