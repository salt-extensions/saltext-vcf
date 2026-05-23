"""Execution module for VCF Automation storage profiles."""

from saltext.vcf.clients import vcfa_storage_profile as c

__virtualname__ = "vcf_vcfa_storage_profile"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all storage profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_storage_profile.list_
    """
    return c.list_(__opts__, profile=profile)


def list_vsphere(profile=None):
    """List vSphere-specific storage profiles."""
    return c.list_vsphere(__opts__, profile=profile)


def get(profile_id, profile=None):
    """Get one storage profile by id."""
    return c.get(__opts__, profile_id, profile=profile)


def get_vsphere(profile_id, profile=None):
    """Get one vSphere storage profile by id."""
    return c.get_vsphere(__opts__, profile_id, profile=profile)


def get_or_none(profile_id, profile=None):
    """Get one storage profile by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, profile_id, profile=profile)


def create_vsphere(spec, profile=None):
    """Create a vSphere storage profile."""
    return c.create_vsphere(__opts__, spec, profile=profile)


def update_vsphere(profile_id, spec, profile=None):
    """Update a vSphere storage profile."""
    return c.update_vsphere(__opts__, profile_id, spec, profile=profile)


def delete(profile_id, profile=None):
    """Delete a storage profile."""
    return c.delete(__opts__, profile_id, profile=profile)
