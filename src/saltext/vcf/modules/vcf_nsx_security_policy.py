"""Execution module for NSX security policies."""

from saltext.vcf.clients import nsx_security_policy as c

__virtualname__ = "vcf_nsx_security_policy"


def __virtual__():
    return __virtualname__


def list_(domain="default", profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_security_policy.list_ <domain>

    """
    return c.list_(__opts__, domain=domain, profile=profile)


def get(policy, domain="default", profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_security_policy.get <policy> <domain>

    """
    return c.get(__opts__, policy, domain=domain, profile=profile)


def create(policy, domain="default", profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_security_policy.create <policy> <domain>

    """
    return c.create(__opts__, policy, domain=domain, profile=profile, **spec)


def delete(policy, domain="default", profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_security_policy.delete <policy> <domain>

    """
    return c.delete(__opts__, policy, domain=domain, profile=profile)
