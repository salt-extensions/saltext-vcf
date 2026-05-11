"""Execution module for SDDC Manager release catalog."""

from saltext.vmware.clients import sddc_releases as c

__virtualname__ = "vmware_sddc_releases"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_releases.list_

    """
    return c.list_(__opts__, profile=profile)


def domain(domain_id, profile=None):
    """Domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_releases.domain <domain_id>

    """
    return c.domain(__opts__, domain_id, profile=profile)


def system(profile=None):
    """System.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_releases.system

    """
    return c.system(__opts__, profile=profile)
