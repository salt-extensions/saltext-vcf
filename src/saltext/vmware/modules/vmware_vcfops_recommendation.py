"""Execution module for VCF Operations recommendations catalog."""

from saltext.vmware.clients import vcfops_recommendation as c

__virtualname__ = "vmware_vcfops_recommendation"


def __virtual__():
    return __virtualname__


def list_(page=0, page_size=1000):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_recommendation.list_ <page> <page_size>

    """
    return c.list_(__opts__, page=page, page_size=page_size)


def get(recommendation_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_recommendation.get <recommendation_id>

    """
    return c.get(__opts__, recommendation_id)
