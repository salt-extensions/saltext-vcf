"""Execution module for SDDC Manager release catalog."""

from saltext.vcf.clients import sddc_releases as c

__virtualname__ = "vcf_sddc_releases"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_releases.list_

    """
    return c.list_(__opts__, profile=profile)


def domain(domain_id, profile=None):
    """Domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_releases.domain <domain_id>

    """
    return c.domain(__opts__, domain_id, profile=profile)


def system(profile=None):
    """System.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_releases.system

    """
    return c.system(__opts__, profile=profile)


def custom_patches(domain_id, profile=None):
    """List async / out-of-band patches registered on the given domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_releases.custom_patches <domain_id>

    """
    return c.custom_patches(__opts__, domain_id, profile=profile)
