"""Execution module for NSX Tier-0 gateways."""

from saltext.vcf.clients import nsx_tier0 as r

__virtualname__ = "vcf_nsx_tier0"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List Tier-0 gateways.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.list_

    """
    return r.list_(__opts__, profile=profile)


def get(tier0, profile=None):
    """Return a Tier-0 gateway by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.get <tier0>

    """
    return r.get(__opts__, tier0, profile=profile)


def bgp_get(tier0, locale_service="default", profile=None):
    """Return the BGP config for a Tier-0 locale-service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.bgp_get <tier0>

    """
    return r.bgp_get(__opts__, tier0, locale_service=locale_service, profile=profile)


def bgp_set(tier0, enabled, locale_service="default", profile=None, **extra):
    """Patch the BGP config for a Tier-0 locale-service (at minimum ``enabled``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.bgp_set <tier0> enabled=False

    """
    return r.bgp_set(
        __opts__, tier0, enabled, locale_service=locale_service, profile=profile, **extra
    )


def ospf_get(tier0, locale_service="default", profile=None):
    """Return the OSPF config for a Tier-0 locale-service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.ospf_get <tier0>

    """
    return r.ospf_get(__opts__, tier0, locale_service=locale_service, profile=profile)


def ospf_set(tier0, enabled, locale_service="default", profile=None, **extra):
    """Patch the OSPF config for a Tier-0 locale-service (at minimum ``enabled``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.ospf_set <tier0> enabled=False

    """
    return r.ospf_set(
        __opts__, tier0, enabled, locale_service=locale_service, profile=profile, **extra
    )


def multicast_get(tier0, locale_service="default", profile=None):
    """Return the multicast config for a Tier-0 locale-service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.multicast_get <tier0>

    """
    return r.multicast_get(__opts__, tier0, locale_service=locale_service, profile=profile)


def multicast_set(tier0, enabled, locale_service="default", profile=None, **extra):
    """Patch the multicast config for a Tier-0 locale-service (at minimum ``enabled``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier0.multicast_set <tier0> enabled=False

    """
    return r.multicast_set(
        __opts__, tier0, enabled, locale_service=locale_service, profile=profile, **extra
    )
