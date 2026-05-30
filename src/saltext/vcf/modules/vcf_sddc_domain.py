"""Execution module for SDDC Manager workload domains."""

from saltext.vcf.clients import sddc_domain as r

__virtualname__ = "vcf_sddc_domain"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List workload domains.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_domain.list_

    """
    return r.list_(__opts__, profile=profile)


def get(domain, profile=None):
    """Return details for a single workload domain by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_domain.get <domain>

    """
    return r.get(__opts__, domain, profile=profile)


def validate(spec, profile=None):
    """Validate a workload domain spec."""
    return r.validate(__opts__, spec, profile=profile)


def create(spec, profile=None):
    """Create a workload domain."""
    return r.create(__opts__, spec, profile=profile)


def update(domain, spec, profile=None):
    """Update a workload domain."""
    return r.update(__opts__, domain, spec, profile=profile)


def delete(domain, profile=None):
    """Delete a workload domain."""
    return r.delete(__opts__, domain, profile=profile)


def mark_for_deletion(domain, profile=None):
    """Mark a workload domain for deletion."""
    return r.mark_for_deletion(__opts__, domain, profile=profile)
