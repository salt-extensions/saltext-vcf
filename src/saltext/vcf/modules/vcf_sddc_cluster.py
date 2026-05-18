"""Execution module for SDDC Manager clusters."""

from saltext.vcf.clients import sddc_cluster as r

__virtualname__ = "vcf_sddc_cluster"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List clusters managed by SDDC Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_cluster.list_

    """
    return r.list_(__opts__, profile=profile)


def get(cluster, profile=None):
    """Return details for a single cluster by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_cluster.get <cluster>

    """
    return r.get(__opts__, cluster, profile=profile)


def create(cluster_spec, profile=None):
    """Create a cluster from the spec documented at POST /v1/clusters.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_cluster.create <cluster_spec>

    """
    return r.create(__opts__, cluster_spec, profile=profile)


def delete(cluster, profile=None):
    """Delete a cluster by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_cluster.delete <cluster>

    """
    return r.delete(__opts__, cluster, profile=profile)
