"""Execution module for vSAN cluster configuration (SOAP)."""

from saltext.vcf.clients import vsan_cluster as c

__virtualname__ = "vcf_vsan_cluster"


def __virtual__():
    return __virtualname__


def get(cluster, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_cluster.get <cluster>

    """
    return c.get(__opts__, cluster, profile=profile)


def reconfigure(cluster, profile=None, **fields):
    """Reconfigure.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_cluster.reconfigure <cluster>

    """
    return c.reconfigure(__opts__, cluster, profile=profile, **fields)


def runtime_info(cluster, profile=None):
    """Runtime info.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vsan_cluster.runtime_info <cluster>

    """
    return c.runtime_info(__opts__, cluster, profile=profile)
