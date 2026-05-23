"""Execution module for VCF Automation resource actions."""

from saltext.vcf.clients import vcfa_resource_action as c

__virtualname__ = "vcf_vcfa_resource_action"


def __virtual__():
    return __virtualname__


def list_(project_id=None, profile=None):
    """List resource actions, optionally filtered by project.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_resource_action.list_
    """
    return c.list_(__opts__, project_id=project_id, profile=profile)


def get(action_id, profile=None):
    """Get one resource action by id."""
    return c.get(__opts__, action_id, profile=profile)


def get_or_none(action_id, profile=None):
    """Get one resource action by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, action_id, profile=profile)


def create(spec, profile=None):
    """Register a resource action."""
    return c.create(__opts__, spec, profile=profile)


def update(action_id, spec, profile=None):
    """Update a resource action."""
    return c.update(__opts__, action_id, spec, profile=profile)


def delete(action_id, profile=None):
    """Delete a resource action."""
    return c.delete(__opts__, action_id, profile=profile)
