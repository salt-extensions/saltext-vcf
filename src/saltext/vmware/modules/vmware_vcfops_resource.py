"""Execution module for VCF Operations resources."""

from saltext.vmware.clients import vcfops_resource as c

__virtualname__ = "vmware_vcfops_resource"


def __virtual__():
    return __virtualname__


def list_(page=0, page_size=1000, **filters):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_resource.list_ <page> <page_size>

    """
    return c.list_(__opts__, page=page, page_size=page_size, **filters)


def get(resource_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_resource.get <resource_id>

    """
    return c.get(__opts__, resource_id)


def relationships(resource_id, **filters):
    """Relationships.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_resource.relationships <resource_id>

    """
    return c.relationships(__opts__, resource_id, **filters)


def stats(resource_id, **filters):
    """Stats.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_resource.stats <resource_id>

    """
    return c.stats(__opts__, resource_id, **filters)
