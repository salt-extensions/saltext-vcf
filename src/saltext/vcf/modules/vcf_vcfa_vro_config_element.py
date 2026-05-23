"""Execution module for VCF Automation vRO configuration elements."""

from saltext.vcf.clients import vcfa_vro_config_element as c

__virtualname__ = "vcf_vcfa_vro_config_element"


def __virtual__():
    return __virtualname__


def list_(category=None, profile=None):
    """List vRO configuration elements, optionally filtered by category id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_vro_config_element.list_
    """
    return c.list_(__opts__, category=category, profile=profile)


def get(config_id, profile=None):
    """Get one configuration element by id."""
    return c.get(__opts__, config_id, profile=profile)


def get_or_none(config_id, profile=None):
    """Get one configuration element by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, config_id, profile=profile)


def create(spec, profile=None):
    """Create a configuration element."""
    return c.create(__opts__, spec, profile=profile)


def update(config_id, spec, profile=None):
    """Update a configuration element."""
    return c.update(__opts__, config_id, spec, profile=profile)


def delete(config_id, profile=None):
    """Delete a configuration element."""
    return c.delete(__opts__, config_id, profile=profile)


def get_attribute(config_id, attribute_name, profile=None):
    """Get a single attribute."""
    return c.get_attribute(__opts__, config_id, attribute_name, profile=profile)


def set_attribute(config_id, attribute_name, attribute_spec, profile=None):
    """Set a single attribute."""
    return c.set_attribute(__opts__, config_id, attribute_name, attribute_spec, profile=profile)
