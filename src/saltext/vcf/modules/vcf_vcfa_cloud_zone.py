"""Execution module for VCF Automation cloud zones."""

from saltext.vcf.clients import vcfa_cloud_zone as c

__virtualname__ = "vcf_vcfa_cloud_zone"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all cloud zones.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_zone.list_
    """
    return c.list_(__opts__, profile=profile)


def get(zone_id, profile=None):
    """Get one zone by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_zone.get <zone_id>
    """
    return c.get(__opts__, zone_id, profile=profile)


def get_or_none(zone_id, profile=None):
    """Get one zone by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, zone_id, profile=profile)


def create(spec, profile=None):
    """Create a cloud zone.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_zone.create '{"name": "z-prod", ...}'
    """
    return c.create(__opts__, spec, profile=profile)


def update(zone_id, spec, profile=None):
    """Update a cloud zone."""
    return c.update(__opts__, zone_id, spec, profile=profile)


def delete(zone_id, profile=None):
    """Delete a cloud zone."""
    return c.delete(__opts__, zone_id, profile=profile)


def computes(zone_id, profile=None):
    """List computes currently bound to the zone."""
    return c.computes(__opts__, zone_id, profile=profile)
