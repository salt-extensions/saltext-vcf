"""Execution module for NSX Management API — cluster status."""

from saltext.vcf.clients import nsx_cluster as c

__virtualname__ = "vcf_nsx_cluster"


def __virtual__():
    return __virtualname__


def status(profile=None):
    """Status.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_cluster.status

    """
    return c.status(__opts__, profile=profile)
