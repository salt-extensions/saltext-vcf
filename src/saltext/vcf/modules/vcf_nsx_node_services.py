"""Execution module for NSX Management API — node services.

Thin wrapper over :mod:`saltext.vcf.clients.nsx_node_services`. Covers
two STIG-912 surfaces exposed under ``/api/v1/node/services``:

- The HTTP service (``/node/services/http``) carrying the
  DoS-mitigation rate/concurrency limits.
- The audit-logging services (``manager``, ``policy``,
  ``async_replicator``, ``http``) whose ``service_properties.logging_level``
  is the API equivalent of ``set service <name> logging-level <level>``.
"""

from saltext.vcf.clients import nsx_node_services as c

__virtualname__ = "vcf_nsx_node_services"


def __virtual__():
    return __virtualname__


# ---------------------------------------------------------------------------
# Generic per-service helpers
# ---------------------------------------------------------------------------


def service_get(service_name, profile=None):
    """Return the config document for ``/api/v1/node/services/{service_name}``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.service_get manager

    """
    return c.service_get(__opts__, service_name, profile=profile)


def service_set(service_name, profile=None, **fields):
    """Merge the supplied ``service_properties`` fields into *service_name*.

    Read-modify-write against ``/api/v1/node/services/{service_name}``.
    Any keyword whose value is ``None`` is dropped.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.service_set manager logging_level=INFO

    """
    return c.service_set(__opts__, service_name, profile=profile, **fields)


# ---------------------------------------------------------------------------
# HTTP service (unchanged public surface — rate-limit knobs)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Audit-logging service passthroughs
# ---------------------------------------------------------------------------


def manager_get(profile=None):
    """Return the NSX ``manager`` service configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.manager_get

    """
    return c.manager_get(__opts__, profile=profile)


def manager_set(profile=None, **fields):
    """Merge ``service_properties`` fields into the NSX ``manager`` service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.manager_set logging_level=INFO

    """
    return c.manager_set(__opts__, profile=profile, **fields)


def policy_get(profile=None):
    """Return the NSX ``policy`` service configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.policy_get

    """
    return c.policy_get(__opts__, profile=profile)


def policy_set(profile=None, **fields):
    """Merge ``service_properties`` fields into the NSX ``policy`` service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.policy_set logging_level=INFO

    """
    return c.policy_set(__opts__, profile=profile, **fields)


def async_replicator_get(profile=None):
    """Return the NSX ``async_replicator`` service configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.async_replicator_get

    """
    return c.async_replicator_get(__opts__, profile=profile)


def async_replicator_set(profile=None, **fields):
    """Merge ``service_properties`` fields into ``async_replicator``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node_services.async_replicator_set logging_level=INFO

    """
    return c.async_replicator_set(__opts__, profile=profile, **fields)
