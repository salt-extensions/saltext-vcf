"""Execution module for VCF Automation ABX actions."""

from saltext.vcf.clients import vcfa_action as c

__virtualname__ = "vcf_vcfa_action"


def __virtual__():
    return __virtualname__


def list_(project_id=None, profile=None):
    """List ABX actions, optionally filtered by project.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_action.list_
    """
    return c.list_(__opts__, project_id=project_id, profile=profile)


def get(action_id, profile=None):
    """Get one action by id."""
    return c.get(__opts__, action_id, profile=profile)


def get_or_none(action_id, profile=None):
    """Get one action by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, action_id, profile=profile)


def create(spec, profile=None):
    """Create an ABX action."""
    return c.create(__opts__, spec, profile=profile)


def update(action_id, spec, profile=None):
    """Update an ABX action."""
    return c.update(__opts__, action_id, spec, profile=profile)


def delete(action_id, profile=None):
    """Delete an ABX action."""
    return c.delete(__opts__, action_id, profile=profile)


def run(action_id, inputs=None, profile=None):
    """Invoke an action on demand.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_action.run <action_id> inputs='{"k": "v"}'
    """
    return c.run(__opts__, action_id, inputs=inputs, profile=profile)


def list_runs(action_id, profile=None):
    """List previous runs of an action."""
    return c.list_runs(__opts__, action_id, profile=profile)
