"""Execution module for SDDC Manager credentials."""

from saltext.vmware.clients import sddc_credentials as r

__virtualname__ = "vmware_sddc_credentials"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List managed credentials.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_credentials.list_

    """
    return r.list_(__opts__, profile=profile)


def rotate(elements, profile=None):
    """Rotate credentials for the supplied resource elements (PATCH /v1/credentials).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_credentials.rotate <elements>

    """
    return r.rotate(__opts__, elements, profile=profile)
