"""Execution module for SDDC Manager appliance info (/v1/sddc-manager)."""

from saltext.vcf.clients import sddc_manager as c

__virtualname__ = "vcf_sddc_manager"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_manager.get

    """
    return c.get(__opts__, profile=profile)
