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
