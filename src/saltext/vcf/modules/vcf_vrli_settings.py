"""Execution module for VCF Operations for Logs (vRLI) appliance settings.

Wraps :mod:`saltext.vcf.clients.vrli_settings`. Some sub-operations
require root SSH access to the appliance — see the docstrings on the
underlying client for the file paths edited.
"""

from saltext.vcf.clients import vrli_settings as c

__virtualname__ = "vcf_vrli_settings"


def __virtual__():
    return __virtualname__


def get_cluster_nodes(profile=None):
    """Return the nodes reported by ``GET /api/v2/cluster/nodes``."""
    return c.get_cluster_nodes(__opts__, profile=profile)


def get_dns_servers(profile=None):
    """Return the IPv4 DNS servers reported by the REST API.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_settings.get_dns_servers
    """
    return c.get_dns_servers(__opts__, profile=profile)


def get_dns_servers_from_appliance(profile=None):
    """SSH read of the on-appliance DNS config (for verification)."""
    return c.get_dns_servers_from_appliance(__opts__, profile=profile)


def set_dns_servers(servers, profile=None):
    """Set the IPv4 DNS servers by rewriting ``10-eth0.network``.

    Requires ``ssh`` sub-block in the pillar. See
    :mod:`saltext.vcf.clients.vrli_settings` for details.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_settings.set_dns_servers '["10.0.0.53","10.0.0.54"]'
    """
    return c.set_dns_servers(__opts__, servers, profile=profile)


def get_session_timeout(profile=None):
    """Return the current session inactivity timeout in seconds.

    Reads ``web.xml`` via SSH.
    """
    return c.get_session_timeout(__opts__, profile=profile)


def set_session_timeout(seconds, profile=None):
    """Set the session inactivity timeout (seconds -> minutes in web.xml).

    Restarts the ``loginsight`` service so Jetty re-reads the descriptor.
    """
    return c.set_session_timeout(__opts__, seconds, profile=profile)
