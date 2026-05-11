"""Execution module for VCF Operations policies and notification rules."""

from saltext.vmware.clients import vcfops_policy as c

__virtualname__ = "vmware_vcfops_policy"


def __virtual__():
    return __virtualname__


def list_():
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_policy.list_

    """
    return c.list_(__opts__)


def get(policy_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_policy.get <policy_id>

    """
    return c.get(__opts__, policy_id)


def notification_rules_list():
    """Notification rules list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_policy.notification_rules_list

    """
    return c.notification_rules_list(__opts__)
