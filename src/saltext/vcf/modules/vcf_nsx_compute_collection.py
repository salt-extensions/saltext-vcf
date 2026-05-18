"""Execution module for NSX compute collections."""

from saltext.vcf.clients import nsx_compute_collection as c

__virtualname__ = "vcf_nsx_compute_collection"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_compute_collection.list_

    """
    return c.list_(__opts__, profile=profile)


def get(collection_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_compute_collection.get <collection_id>

    """
    return c.get(__opts__, collection_id, profile=profile)
