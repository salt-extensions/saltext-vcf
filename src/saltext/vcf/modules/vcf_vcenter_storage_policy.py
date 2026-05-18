"""Execution module for vCenter storage policies."""

from saltext.vcf.clients import vcenter_storage_policy as c

__virtualname__ = "vcf_vcenter_storage_policy"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.list_

    """
    return c.list_(__opts__, profile=profile)


def get(policy, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.get <policy>

    """
    return c.get(__opts__, policy, profile=profile)
