"""Execution module for SDDC Manager vCenter registrations."""

from saltext.vcf.clients import sddc_vcenters as c

__virtualname__ = "vcf_sddc_vcenters"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_vcenters.list_

    """
    return c.list_(__opts__, profile=profile)


def get(vcenter_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_vcenters.get <vcenter_id>

    """
    return c.get(__opts__, vcenter_id, profile=profile)
