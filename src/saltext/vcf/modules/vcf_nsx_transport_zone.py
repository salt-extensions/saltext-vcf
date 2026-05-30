"""Execution module for NSX transport zones."""

from saltext.vcf.clients import nsx_transport_zone as c

__virtualname__ = "vcf_nsx_transport_zone"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_transport_zone.list_

    """
    return c.list_(__opts__, profile=profile)


def get(zone_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_transport_zone.get <zone_id>

    """
    return c.get(__opts__, zone_id, profile=profile)


def create(name, zone_type, profile=None, **spec):
    """Create a transport zone."""
    return c.create(__opts__, name, zone_type, profile=profile, **spec)


def update(zone_id, profile=None, **spec):
    """Update a transport zone by id."""
    return c.update(__opts__, zone_id, profile=profile, **spec)


def delete(zone_id, profile=None):
    """Delete a transport zone by id."""
    return c.delete(__opts__, zone_id, profile=profile)
