"""Execution module for VCF Automation cloud templates (blueprints)."""

from saltext.vcf.clients import vcfa_cloud_template as c

__virtualname__ = "vcf_vcfa_cloud_template"


def __virtual__():
    return __virtualname__


def list_(project_id=None, profile=None):
    """List cloud templates, optionally filtered by project.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_template.list_
        salt '*' vcf_vcfa_cloud_template.list_ project_id=<id>
    """
    return c.list_(__opts__, project_id=project_id, profile=profile)


def get(blueprint_id, profile=None):
    """Get one cloud template by id."""
    return c.get(__opts__, blueprint_id, profile=profile)


def get_or_none(blueprint_id, profile=None):
    """Get one cloud template by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, blueprint_id, profile=profile)


def create(spec, profile=None):
    """Create a cloud template."""
    return c.create(__opts__, spec, profile=profile)


def update(blueprint_id, spec, profile=None):
    """Update a cloud template."""
    return c.update(__opts__, blueprint_id, spec, profile=profile)


def delete(blueprint_id, profile=None):
    """Delete a cloud template."""
    return c.delete(__opts__, blueprint_id, profile=profile)


def list_versions(blueprint_id, profile=None):
    """List released versions of a cloud template."""
    return c.list_versions(__opts__, blueprint_id, profile=profile)


def get_version(blueprint_id, version_id, profile=None):
    """Get one version by id."""
    return c.get_version(__opts__, blueprint_id, version_id, profile=profile)


def create_version(blueprint_id, spec, profile=None):
    """Cut a new version of a cloud template (and optionally release it)."""
    return c.create_version(__opts__, blueprint_id, spec, profile=profile)


def release_version(blueprint_id, version_id, profile=None):
    """Release an existing version to the catalog."""
    return c.release_version(__opts__, blueprint_id, version_id, profile=profile)


def unrelease_version(blueprint_id, version_id, profile=None):
    """Unrelease a version from the catalog."""
    return c.unrelease_version(__opts__, blueprint_id, version_id, profile=profile)
