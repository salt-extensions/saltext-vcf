"""Execution module for VCF Automation tenants / organizations.

Thin passthrough around :mod:`saltext.vcf.clients.vcfa_organization`.
"""

from saltext.vcf.clients import vcfa_organization as c

__virtualname__ = "vcf_vcfa_organization"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all orgs visible to the caller.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_organization.list_
    """
    return c.list_(__opts__, profile=profile)


def get(org_id, profile=None):
    """Get one org by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_organization.get <org_id>
    """
    return c.get(__opts__, org_id, profile=profile)


def get_or_none(org_id, profile=None):
    """Get one org by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, org_id, profile=profile)


def create(spec, profile=None):
    """Create a new tenant / organization.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_organization.create '{"displayName": "Acme", "description": "..."}'
    """
    return c.create(__opts__, spec, profile=profile)


def update(org_id, spec, profile=None):
    """Patch an existing org."""
    return c.update(__opts__, org_id, spec, profile=profile)


def delete(org_id, profile=None):
    """Delete an org."""
    return c.delete(__opts__, org_id, profile=profile)


def list_services(org_id, profile=None):
    """List service definitions attached to the org."""
    return c.list_services(__opts__, org_id, profile=profile)


def enable_service(org_id, service_definition_id, profile=None):
    """Enable a service definition on the org.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_organization.enable_service <org_id> <service_definition_id>
    """
    return c.enable_service(__opts__, org_id, service_definition_id, profile=profile)


def disable_service(org_id, service_definition_id, profile=None):
    """Disable / detach a service definition from the org."""
    return c.disable_service(__opts__, org_id, service_definition_id, profile=profile)
