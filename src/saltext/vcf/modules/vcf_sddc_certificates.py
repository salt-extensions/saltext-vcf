"""Execution module for SDDC Manager certificates (per workload domain)."""

from saltext.vcf.clients import sddc_certificates as c

__virtualname__ = "vcf_sddc_certificates"


def __virtual__():
    return __virtualname__


def list_(domain_id, profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_certificates.list_ <domain_id>

    """
    return c.list_(__opts__, domain_id, profile=profile)


def list_csrs(domain_id, profile=None):
    """List csrs.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_certificates.list_csrs <domain_id>

    """
    return c.list_csrs(__opts__, domain_id, profile=profile)


def create_csrs(domain_id, csr_specs, profile=None):
    """Create csrs.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_certificates.create_csrs <domain_id> <csr_specs>

    """
    return c.create_csrs(__opts__, domain_id, csr_specs, profile=profile)


def install_certificates(domain_id, cert_specs, profile=None):
    """Install certificates.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_certificates.install_certificates <domain_id> <cert_specs>

    """
    return c.install_certificates(__opts__, domain_id, cert_specs, profile=profile)
