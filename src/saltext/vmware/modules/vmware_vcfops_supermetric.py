"""Execution module for VCF Operations super metrics."""

from saltext.vmware.clients import vcfops_supermetric as c

__virtualname__ = "vmware_vcfops_supermetric"


def __virtual__():
    return __virtualname__


def list_(page=0, page_size=1000):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_supermetric.list_ <page> <page_size>

    """
    return c.list_(__opts__, page=page, page_size=page_size)


def get(supermetric_id):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_supermetric.get <supermetric_id>

    """
    return c.get(__opts__, supermetric_id)


def create(supermetric_spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_supermetric.create <supermetric_spec>

    """
    return c.create(__opts__, supermetric_spec)


def update(supermetric_id, supermetric_spec):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_supermetric.update <supermetric_id> <supermetric_spec>

    """
    return c.update(__opts__, supermetric_id, supermetric_spec)


def delete(supermetric_id):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_supermetric.delete <supermetric_id>

    """
    return c.delete(__opts__, supermetric_id)
