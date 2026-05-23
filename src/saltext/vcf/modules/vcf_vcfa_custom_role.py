"""Execution module for VCF Automation IAM custom roles."""

from saltext.vcf.clients import vcfa_custom_role as c

__virtualname__ = "vcf_vcfa_custom_role"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List custom roles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_custom_role.list_
    """
    return c.list_(__opts__, profile=profile)


def get(role_id, profile=None):
    """Get one custom role by id."""
    return c.get(__opts__, role_id, profile=profile)


def get_or_none(role_id, profile=None):
    """Get one custom role by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, role_id, profile=profile)


def create(spec, profile=None):
    """Create a custom role."""
    return c.create(__opts__, spec, profile=profile)


def update(role_id, spec, profile=None):
    """Update a custom role."""
    return c.update(__opts__, role_id, spec, profile=profile)


def delete(role_id, profile=None):
    """Delete a custom role."""
    return c.delete(__opts__, role_id, profile=profile)
