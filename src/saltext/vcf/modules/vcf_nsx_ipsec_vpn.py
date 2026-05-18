"""Execution module for NSX IPsec VPN (T7)."""

from saltext.vcf.clients import nsx_ipsec_vpn as vpn

__virtualname__ = "vcf_nsx_ipsec_vpn"


def __virtual__():
    return __virtualname__


# IKE profiles


def list_ike_profiles(profile=None):
    """List IKE profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.list_ike_profiles
    """
    return vpn.list_ike_profiles(__opts__, profile=profile)


def get_ike_profile(ike_profile, profile=None):
    """Return one IKE profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.get_ike_profile <ike_profile>
    """
    return vpn.get_ike_profile(__opts__, ike_profile, profile=profile)


def create_ike_profile(ike_profile, profile=None, **spec):
    """Create / update an IKE profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.create_ike_profile <ike_profile> ike_version=IKE_V2
    """
    return vpn.create_ike_profile(__opts__, ike_profile, profile=profile, **spec)


def delete_ike_profile(ike_profile, profile=None):
    """Delete an IKE profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.delete_ike_profile <ike_profile>
    """
    return vpn.delete_ike_profile(__opts__, ike_profile, profile=profile)


# Tunnel profiles


def list_tunnel_profiles(profile=None):
    """List IPsec tunnel profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.list_tunnel_profiles
    """
    return vpn.list_tunnel_profiles(__opts__, profile=profile)


def get_tunnel_profile(tunnel_profile, profile=None):
    """Return one tunnel profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.get_tunnel_profile <tunnel_profile>
    """
    return vpn.get_tunnel_profile(__opts__, tunnel_profile, profile=profile)


def create_tunnel_profile(tunnel_profile, profile=None, **spec):
    """Create / update a tunnel profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.create_tunnel_profile <tunnel_profile>
    """
    return vpn.create_tunnel_profile(__opts__, tunnel_profile, profile=profile, **spec)


def delete_tunnel_profile(tunnel_profile, profile=None):
    """Delete a tunnel profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.delete_tunnel_profile <tunnel_profile>
    """
    return vpn.delete_tunnel_profile(__opts__, tunnel_profile, profile=profile)


# DPD profiles


def list_dpd_profiles(profile=None):
    """List DPD (Dead Peer Detection) profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.list_dpd_profiles
    """
    return vpn.list_dpd_profiles(__opts__, profile=profile)


def get_dpd_profile(dpd_profile, profile=None):
    """Return one DPD profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.get_dpd_profile <dpd_profile>
    """
    return vpn.get_dpd_profile(__opts__, dpd_profile, profile=profile)


def create_dpd_profile(dpd_profile, profile=None, **spec):
    """Create / update a DPD profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.create_dpd_profile <dpd_profile>
    """
    return vpn.create_dpd_profile(__opts__, dpd_profile, profile=profile, **spec)


def delete_dpd_profile(dpd_profile, profile=None):
    """Delete a DPD profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.delete_dpd_profile <dpd_profile>
    """
    return vpn.delete_dpd_profile(__opts__, dpd_profile, profile=profile)


# Services


def list_services(tier0, locale, profile=None):
    """List IPsec VPN services under a tier-0 locale.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.list_services <tier0> <locale>
    """
    return vpn.list_services(__opts__, tier0, locale, profile=profile)


def get_service(tier0, locale, service, profile=None):
    """Return one VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.get_service <tier0> <locale> <service>
    """
    return vpn.get_service(__opts__, tier0, locale, service, profile=profile)


def create_service(tier0, locale, service, profile=None, **spec):
    """Create / update a VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.create_service <tier0> <locale> <service> enabled=True
    """
    return vpn.create_service(__opts__, tier0, locale, service, profile=profile, **spec)


def delete_service(tier0, locale, service, profile=None):
    """Delete a VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.delete_service <tier0> <locale> <service>
    """
    return vpn.delete_service(__opts__, tier0, locale, service, profile=profile)


# Sessions


def list_sessions(tier0, locale, service, profile=None):
    """List sessions on a VPN service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.list_sessions <tier0> <locale> <service>
    """
    return vpn.list_sessions(__opts__, tier0, locale, service, profile=profile)


def get_session(tier0, locale, service, session, profile=None):
    """Return one VPN session.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.get_session <tier0> <locale> <service> <session>
    """
    return vpn.get_session(__opts__, tier0, locale, service, session, profile=profile)


def create_session(tier0, locale, service, session, resource_type, profile=None, **spec):
    """Create / update a VPN session.

    *resource_type* is ``PolicyBasedIPSecVpnSession`` or ``RouteBasedIPSecVpnSession``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.create_session <t0> <loc> <svc> <sess> PolicyBasedIPSecVpnSession
    """
    return vpn.create_session(
        __opts__, tier0, locale, service, session, resource_type, profile=profile, **spec
    )


def delete_session(tier0, locale, service, session, profile=None):
    """Delete a VPN session.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ipsec_vpn.delete_session <tier0> <locale> <service> <session>
    """
    return vpn.delete_session(__opts__, tier0, locale, service, session, profile=profile)
