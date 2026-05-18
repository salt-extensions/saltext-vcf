"""Execution module for NSX transport nodes."""

from saltext.vcf.clients import nsx_transport_node as c

__virtualname__ = "vcf_nsx_transport_node"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_transport_node.list_

    """
    return c.list_(__opts__, profile=profile)


def get(node_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_transport_node.get <node_id>

    """
    return c.get(__opts__, node_id, profile=profile)
