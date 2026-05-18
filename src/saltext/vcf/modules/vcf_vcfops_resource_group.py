"""Execution module for VCF Operations custom resource groups."""

from saltext.vcf.clients import vcfops_resource_group as c

__virtualname__ = "vcf_vcfops_resource_group"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_resource_group.list_

    """
    return c.list_(__opts__, profile=profile)


def get(group_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_resource_group.get <group_id>

    """
    return c.get(__opts__, group_id, profile=profile)


def create(group_spec, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_resource_group.create <group_spec>

    """
    return c.create(__opts__, group_spec, profile=profile)


def update(group_id, group_spec, profile=None):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_resource_group.update <group_id> <group_spec>

    """
    return c.update(__opts__, group_id, group_spec, profile=profile)


def delete(group_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_resource_group.delete <group_id>

    """
    return c.delete(__opts__, group_id, profile=profile)
