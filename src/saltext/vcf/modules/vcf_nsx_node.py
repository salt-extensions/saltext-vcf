"""Execution module for NSX Management API — node info."""

from saltext.vcf.clients import nsx_node as c

__virtualname__ = "vcf_nsx_node"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_node.get

    """
    return c.get(__opts__, profile=profile)
