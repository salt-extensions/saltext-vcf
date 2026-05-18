"""Execution module for VCF Operations adapter kinds."""

from saltext.vcf.clients import vcfops_adapter as c

__virtualname__ = "vcf_vcfops_adapter"


def __virtual__():
    return __virtualname__


def list_():
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.list_

    """
    return c.list_(__opts__)


def get(kind_key):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.get <kind_key>

    """
    return c.get(__opts__, kind_key)
