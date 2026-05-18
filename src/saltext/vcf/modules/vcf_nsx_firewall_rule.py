"""Execution module for NSX distributed firewall rules."""

from saltext.vcf.clients import nsx_firewall_rule as c

__virtualname__ = "vcf_nsx_firewall_rule"


def __virtual__():
    return __virtualname__


def list_(policy, domain="default", profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_firewall_rule.list_ <policy> <domain>

    """
    return c.list_(__opts__, policy, domain=domain, profile=profile)


def get(rule, policy, domain="default", profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_firewall_rule.get <rule> <policy> <domain>

    """
    return c.get(__opts__, rule, policy, domain=domain, profile=profile)


def create(rule, policy, domain="default", profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_firewall_rule.create <rule> <policy> <domain>

    """
    return c.create(__opts__, rule, policy, domain=domain, profile=profile, **spec)


def delete(rule, policy, domain="default", profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_firewall_rule.delete <rule> <policy> <domain>

    """
    return c.delete(__opts__, rule, policy, domain=domain, profile=profile)
