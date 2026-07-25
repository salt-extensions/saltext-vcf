"""Execution module for NSX Management API — telemetry / CEIP configuration."""

from saltext.vcf.clients import nsx_telemetry as c

__virtualname__ = "vcf_nsx_telemetry"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Return the NSX Manager telemetry / CEIP configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_telemetry.get

    """
    return c.get(__opts__, profile=profile)


def set_optin(optin, profile=None):
    """Set the CEIP ``optin`` flag on the NSX Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_telemetry.set_optin optin=False

    """
    return c.set_optin(__opts__, optin, profile=profile)
