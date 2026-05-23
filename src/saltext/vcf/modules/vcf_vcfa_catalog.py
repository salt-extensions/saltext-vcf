"""Execution module for VCF Automation catalog (items + sources)."""

from saltext.vcf.clients import vcfa_catalog as c

__virtualname__ = "vcf_vcfa_catalog"


def __virtual__():
    return __virtualname__


def list_items(project_id=None, profile=None):
    """List catalog items, optionally filtered by project.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_catalog.list_items
    """
    return c.list_items(__opts__, project_id=project_id, profile=profile)


def get_item(item_id, profile=None):
    """Get one catalog item by id."""
    return c.get_item(__opts__, item_id, profile=profile)


def get_item_or_none(item_id, profile=None):
    """Get one catalog item by id, or ``None`` on 404."""
    return c.get_item_or_none(__opts__, item_id, profile=profile)


def request_item(item_id, request_spec, profile=None):
    """Submit a catalog request.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_catalog.request_item <item_id> '{"projectId": "...", ...}'
    """
    return c.request_item(__opts__, item_id, request_spec, profile=profile)


def list_sources(profile=None):
    """List catalog sources."""
    return c.list_sources(__opts__, profile=profile)


def get_source(source_id, profile=None):
    """Get one catalog source by id."""
    return c.get_source(__opts__, source_id, profile=profile)


def create_source(spec, profile=None):
    """Create a catalog source."""
    return c.create_source(__opts__, spec, profile=profile)


def update_source(source_id, spec, profile=None):
    """Update a catalog source."""
    return c.update_source(__opts__, source_id, spec, profile=profile)


def delete_source(source_id, profile=None):
    """Delete a catalog source."""
    return c.delete_source(__opts__, source_id, profile=profile)
