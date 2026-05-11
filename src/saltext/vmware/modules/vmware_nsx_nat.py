"""Execution module for NSX NAT rules."""

from saltext.vmware.clients import nsx_nat as c

__virtualname__ = "vmware_nsx_nat"


def __virtual__():
    return __virtualname__


def list_(t1, scope="USER", profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_nat.list_ <t1> <scope>

    """
    return c.list_(__opts__, t1, scope=scope, profile=profile)


def get(rule, t1, scope="USER", profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_nat.get <rule> <t1> <scope>

    """
    return c.get(__opts__, rule, t1, scope=scope, profile=profile)


def get_or_none(rule, t1, scope="USER", profile=None):
    """Get or none.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_nat.get_or_none <rule> <t1> <scope>

    """
    return c.get_or_none(__opts__, rule, t1, scope=scope, profile=profile)


def create(rule, t1, scope="USER", profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_nat.create <rule> <t1> <scope>

    """
    return c.create(__opts__, rule, t1, scope=scope, profile=profile, **spec)


def delete(rule, t1, scope="USER", profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_nat.delete <rule> <t1> <scope>

    """
    return c.delete(__opts__, rule, t1, scope=scope, profile=profile)


def list_t0(t0, scope="USER", profile=None):
    """List t0.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_nat.list_t0 <t0> <scope>

    """
    return c.list_t0(__opts__, t0, scope=scope, profile=profile)
