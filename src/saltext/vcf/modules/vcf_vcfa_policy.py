"""Execution module for VCF Automation policies."""

from saltext.vcf.clients import vcfa_policy as c

__virtualname__ = "vcf_vcfa_policy"


def __virtual__():
    return __virtualname__


def list_(project_id=None, profile=None):
    """List policies, optionally filtered by project.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_policy.list_
    """
    return c.list_(__opts__, project_id=project_id, profile=profile)


def get(policy_id, profile=None):
    """Get one policy by id."""
    return c.get(__opts__, policy_id, profile=profile)


def get_or_none(policy_id, profile=None):
    """Get one policy by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, policy_id, profile=profile)


def create(spec, profile=None):
    """Create a policy."""
    return c.create(__opts__, spec, profile=profile)


def update(policy_id, spec, profile=None):
    """Update a policy."""
    return c.update(__opts__, policy_id, spec, profile=profile)


def delete(policy_id, profile=None):
    """Delete a policy."""
    return c.delete(__opts__, policy_id, profile=profile)


def list_types(profile=None):
    """List supported policy ``typeId`` values."""
    return c.list_types(__opts__, profile=profile)
