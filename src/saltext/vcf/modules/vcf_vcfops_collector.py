"""Execution module for VCF Operations collectors + collector groups."""

from saltext.vcf.clients import vcfops_collector as c

__virtualname__ = "vcf_vcfops_collector"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.list_

    """
    return c.list_(__opts__, profile=profile)


def get(collector_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.get <collector_id>

    """
    return c.get(__opts__, collector_id, profile=profile)


def delete(collector_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.delete <collector_id>

    """
    return c.delete(__opts__, collector_id, profile=profile)


def groups_list(profile=None):
    """Groups list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.groups_list

    """
    return c.groups_list(__opts__, profile=profile)


def groups_get(group_id, profile=None):
    """Groups get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.groups_get <group_id>

    """
    return c.groups_get(__opts__, group_id, profile=profile)


def groups_create(group_spec, profile=None):
    """Groups create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.groups_create <group_spec>

    """
    return c.groups_create(__opts__, group_spec, profile=profile)


def groups_update(group_id, group_spec, profile=None):
    """Groups update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.groups_update <group_id> <group_spec>

    """
    return c.groups_update(__opts__, group_id, group_spec, profile=profile)


def groups_delete(group_id, profile=None):
    """Groups delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_collector.groups_delete <group_id>

    """
    return c.groups_delete(__opts__, group_id, profile=profile)
