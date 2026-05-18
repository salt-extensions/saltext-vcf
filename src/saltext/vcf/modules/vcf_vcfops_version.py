"""Execution module for VCF Operations versions."""

from saltext.vcf.clients import vcfops_version as c

__virtualname__ = "vcf_vcfops_version"


def __virtual__():
    return __virtualname__


def get():
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_version.get

    """
    return c.get(__opts__)
