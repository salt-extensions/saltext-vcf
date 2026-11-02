"""Execution module for vSphere service-instance information (SOAP)."""

from saltext.vcf.clients import vim_info as c

__virtualname__ = "vcf_vim_info"


def __virtual__():
    return __virtualname__


def system_info(profile=None):
    """Return system information about the connected vSphere service.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_info.system_info
    """
    return c.about(__opts__, profile=profile)
