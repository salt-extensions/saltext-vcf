"""Execution module for VCF Automation network profiles."""

from saltext.vcf.clients import vcfa_network_profile as c

__virtualname__ = "vcf_vcfa_network_profile"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all network profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_network_profile.list_
    """
    return c.list_(__opts__, profile=profile)


def get(profile_id, profile=None):
    """Get one network profile by id."""
    return c.get(__opts__, profile_id, profile=profile)


def get_or_none(profile_id, profile=None):
    """Get one network profile by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, profile_id, profile=profile)


def create(spec, profile=None):
    """Create a network profile."""
    return c.create(__opts__, spec, profile=profile)


def update(profile_id, spec, profile=None):
    """Update a network profile."""
    return c.update(__opts__, profile_id, spec, profile=profile)


def delete(profile_id, profile=None):
    """Delete a network profile."""
    return c.delete(__opts__, profile_id, profile=profile)
