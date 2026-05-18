"""Execution module for NSX IP pools."""

from saltext.vcf.clients import nsx_ip_pool as c

__virtualname__ = "vcf_nsx_ip_pool"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.list_

    """
    return c.list_(__opts__, profile=profile)


def get(pool_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.get <pool_id>

    """
    return c.get(__opts__, pool_id, profile=profile)


def create(pool_id, profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.create <pool_id>

    """
    return c.create(__opts__, pool_id, profile=profile, **spec)


def delete(pool_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.delete <pool_id>

    """
    return c.delete(__opts__, pool_id, profile=profile)


def list_subnets(pool_id, profile=None):
    """List subnets.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.list_subnets <pool_id>

    """
    return c.list_subnets(__opts__, pool_id, profile=profile)


def create_subnet(pool_id, subnet_id, profile=None, **spec):
    """Create subnet.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.create_subnet <pool_id> <subnet_id>

    """
    return c.create_subnet(__opts__, pool_id, subnet_id, profile=profile, **spec)


def delete_subnet(pool_id, subnet_id, profile=None):
    """Delete subnet.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.delete_subnet <pool_id> <subnet_id>

    """
    return c.delete_subnet(__opts__, pool_id, subnet_id, profile=profile)


def list_allocations(pool_id, profile=None):
    """List allocations.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ip_pool.list_allocations <pool_id>

    """
    return c.list_allocations(__opts__, pool_id, profile=profile)
