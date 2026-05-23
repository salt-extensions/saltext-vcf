"""Execution module for VCF Automation ABX action secrets."""

from saltext.vcf.clients import vcfa_action_secret as c

__virtualname__ = "vcf_vcfa_action_secret"


def __virtual__():
    return __virtualname__


def list_(project_id=None, profile=None):
    """List action secrets, optionally filtered by project.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_action_secret.list_
    """
    return c.list_(__opts__, project_id=project_id, profile=profile)


def get(secret_id, profile=None):
    """Get one action secret by id."""
    return c.get(__opts__, secret_id, profile=profile)


def get_or_none(secret_id, profile=None):
    """Get one action secret by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, secret_id, profile=profile)


def create(spec, profile=None):
    """Create an action secret."""
    return c.create(__opts__, spec, profile=profile)


def update(secret_id, spec, profile=None):
    """Update an action secret."""
    return c.update(__opts__, secret_id, spec, profile=profile)


def delete(secret_id, profile=None):
    """Delete an action secret."""
    return c.delete(__opts__, secret_id, profile=profile)
