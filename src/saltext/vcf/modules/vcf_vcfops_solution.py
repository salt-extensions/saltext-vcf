"""Execution module for VCF Operations solutions / management packs."""

from saltext.vcf.clients import vcfops_solution as c

__virtualname__ = "vcf_vcfops_solution"


def __virtual__():
    return __virtualname__


def list_():
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_solution.list_

    """
    return c.list_(__opts__)


def get(solution_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_solution.get <solution_id>

    """
    return c.get(__opts__, solution_id)
