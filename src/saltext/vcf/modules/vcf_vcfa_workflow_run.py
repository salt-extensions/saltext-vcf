"""Execution module for VCF Automation vRO workflow runs."""

from saltext.vcf.clients import vcfa_workflow_run as c

__virtualname__ = "vcf_vcfa_workflow_run"


def __virtual__():
    return __virtualname__


def list_(workflow_id, profile=None):
    """List executions of a workflow.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_workflow_run.list_ <workflow_id>
    """
    return c.list_(__opts__, workflow_id, profile=profile)


def get(workflow_id, run_id, profile=None):
    """Get a single workflow execution."""
    return c.get(__opts__, workflow_id, run_id, profile=profile)


def get_or_none(workflow_id, run_id, profile=None):
    """Get a single workflow execution, or ``None`` on 404."""
    return c.get_or_none(__opts__, workflow_id, run_id, profile=profile)


def start(workflow_id, parameters=None, profile=None):
    """Start a workflow execution.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_workflow_run.start <workflow_id> '[{"name": "x", "type": "string", "value": "y"}]'
    """
    return c.start(__opts__, workflow_id, parameters=parameters, profile=profile)


def cancel(workflow_id, run_id, profile=None):
    """Cancel a running workflow execution."""
    return c.cancel(__opts__, workflow_id, run_id, profile=profile)


def logs(workflow_id, run_id, profile=None):
    """Return logs of a workflow execution."""
    return c.logs(__opts__, workflow_id, run_id, profile=profile)


def state(workflow_id, run_id, profile=None):
    """Return the ``state`` of a workflow execution."""
    return c.state(__opts__, workflow_id, run_id, profile=profile)
