"""Execution module for VCF Operations task status."""

from saltext.vcf.clients import vcfops_task as c

__virtualname__ = "vcf_vcfops_task"


def __virtual__():
    return __virtualname__


def list_(page=0, page_size=1000):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_task.list_ <page> <page_size>

    """
    return c.list_(__opts__, page=page, page_size=page_size)


def get(task_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_task.get <task_id>

    """
    return c.get(__opts__, task_id)
