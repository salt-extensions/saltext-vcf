"""Execution module for NSX L2 VPN (services + sessions)."""

from saltext.vmware.clients import nsx_l2_vpn as c

__virtualname__ = "vmware_nsx_l2_vpn"


def __virtual__():
    return __virtualname__


def list_services(tier0, locale, profile=None):
    """List L2 VPN services under a tier-0 locale.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.list_services <tier0> <locale>
    """
    return c.list_services(__opts__, tier0, locale, profile=profile)


def get_service(tier0, locale, service, profile=None):
    """Return one L2 VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.get_service <tier0> <locale> <service>
    """
    return c.get_service(__opts__, tier0, locale, service, profile=profile)


def create_service(tier0, locale, service, profile=None, **spec):
    """Create / update an L2 VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.create_service <tier0> <locale> <service> mode=SERVER
    """
    return c.create_service(__opts__, tier0, locale, service, profile=profile, **spec)


def delete_service(tier0, locale, service, profile=None):
    """Delete an L2 VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.delete_service <tier0> <locale> <service>
    """
    return c.delete_service(__opts__, tier0, locale, service, profile=profile)


def list_sessions(tier0, locale, service, profile=None):
    """List sessions on an L2 VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.list_sessions <tier0> <locale> <service>
    """
    return c.list_sessions(__opts__, tier0, locale, service, profile=profile)


def get_session(tier0, locale, service, session, profile=None):
    """Return one L2 VPN session.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.get_session <tier0> <locale> <service> <session>
    """
    return c.get_session(__opts__, tier0, locale, service, session, profile=profile)


def create_session(tier0, locale, service, session, profile=None, **spec):
    """Create / update an L2 VPN session.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.create_session <tier0> <locale> <svc> <sess> transport_tunnels='["..."]'
    """
    return c.create_session(__opts__, tier0, locale, service, session, profile=profile, **spec)


def delete_session(tier0, locale, service, session, profile=None):
    """Delete an L2 VPN session.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_l2_vpn.delete_session <tier0> <locale> <service> <session>
    """
    return c.delete_session(__opts__, tier0, locale, service, session, profile=profile)
