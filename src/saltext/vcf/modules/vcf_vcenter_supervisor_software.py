"""Execution module for Supervisor cluster software/lifecycle (VKS)."""

from saltext.vcf.clients import vcenter_supervisor_software as c

__virtualname__ = "vcf_vcenter_supervisor_software"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_software.list_

    """
    return c.list_(__opts__, profile=profile)


def get(cluster_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_software.get <cluster_id>

    """
    return c.get(__opts__, cluster_id, profile=profile)


def upgrade(cluster_id, upgrade_spec, profile=None):
    """Upgrade.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_software.upgrade <cluster_id> <upgrade_spec>

    """
    return c.upgrade(__opts__, cluster_id, upgrade_spec, profile=profile)
