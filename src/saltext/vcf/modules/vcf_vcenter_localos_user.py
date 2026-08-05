"""Execution module for vCenter Server Appliance (VAMI) local OS user accounts."""

from saltext.vcf.clients import vcenter_localos_user as c

__virtualname__ = "vcf_vcenter_localos_user"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_localos_user.list_

    """
    return c.list_(__opts__, profile=profile)


def get(username, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_localos_user.get <username>

    """
    return c.get(__opts__, username, profile=profile)


def create(username, password, roles, profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_localos_user.create bob '["operator"]' password=secret

    """
    return c.create(__opts__, username, password, roles, profile=profile, **spec)


def update(username, profile=None, **spec):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_localos_user.update bob enabled=False

    """
    return c.update(__opts__, username, profile=profile, **spec)


def delete(username, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_localos_user.delete bob

    """
    return c.delete(__opts__, username, profile=profile)
