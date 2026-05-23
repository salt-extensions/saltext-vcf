"""Execution module for VCF Automation projects."""

from saltext.vcf.clients import vcfa_project as c

__virtualname__ = "vcf_vcfa_project"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all projects.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_project.list_
    """
    return c.list_(__opts__, profile=profile)


def get(project_id, profile=None):
    """Get one project by id."""
    return c.get(__opts__, project_id, profile=profile)


def get_or_none(project_id, profile=None):
    """Get one project by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, project_id, profile=profile)


def create(spec, profile=None):
    """Create a project."""
    return c.create(__opts__, spec, profile=profile)


def update(project_id, spec, profile=None):
    """Update a project."""
    return c.update(__opts__, project_id, spec, profile=profile)


def delete(project_id, profile=None):
    """Delete a project."""
    return c.delete(__opts__, project_id, profile=profile)


def resources(project_id, profile=None):
    """List provisioned resources for a project."""
    return c.resources(__opts__, project_id, profile=profile)
