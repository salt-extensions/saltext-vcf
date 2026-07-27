"""Execution module for NSX Tier-1 gateways."""

from saltext.vcf.clients import nsx_tier1 as r

__virtualname__ = "vcf_nsx_tier1"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List Tier-1 gateways.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier1.list_

    """
    return r.list_(__opts__, profile=profile)


def get(tier1, profile=None):
    """Return a Tier-1 gateway by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier1.get <tier1>

    """
    return r.get(__opts__, tier1, profile=profile)


def create(tier1, profile=None, **spec):
    """Create or update a Tier-1 gateway (PUT).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier1.create <tier1>

    """
    return r.create(__opts__, tier1, profile=profile, **spec)


def delete(tier1, profile=None):
    """Delete a Tier-1 gateway by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier1.delete <tier1>

    """
    return r.delete(__opts__, tier1, profile=profile)


def multicast_get(tier1, locale_service="default", profile=None):
    """Return the multicast config for a Tier-1 locale-service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier1.multicast_get <tier1>

    """
    return r.multicast_get(__opts__, tier1, locale_service=locale_service, profile=profile)


def multicast_set(tier1, enabled, locale_service="default", profile=None, **extra):
    """Patch the multicast config for a Tier-1 locale-service (at minimum ``enabled``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_tier1.multicast_set <tier1> enabled=False

    """
    return r.multicast_set(
        __opts__, tier1, enabled, locale_service=locale_service, profile=profile, **extra
    )
