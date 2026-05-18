"""Execution module for VCF Operations maintenance schedules."""

from saltext.vcf.clients import vcfops_maintenance as c

__virtualname__ = "vcf_vcfops_maintenance"


def __virtual__():
    return __virtualname__


def list_(page=0, page_size=1000):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_maintenance.list_ <page> <page_size>

    """
    return c.list_(__opts__, page=page, page_size=page_size)


def get(schedule_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_maintenance.get <schedule_id>

    """
    return c.get(__opts__, schedule_id)


def create(schedule_spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_maintenance.create <schedule_spec>

    """
    return c.create(__opts__, schedule_spec)


def update(schedule_id, schedule_spec):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_maintenance.update <schedule_id> <schedule_spec>

    """
    return c.update(__opts__, schedule_id, schedule_spec)


def delete(schedule_id):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_maintenance.delete <schedule_id>

    """
    return c.delete(__opts__, schedule_id)
