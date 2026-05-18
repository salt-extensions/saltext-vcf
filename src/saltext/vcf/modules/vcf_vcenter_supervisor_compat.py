"""Execution module for Supervisor pre-enable compatibility probes (VKS)."""

from saltext.vcf.clients import vcenter_supervisor_compat as c

__virtualname__ = "vcf_vcenter_supervisor_compat"


def __virtual__():
    return __virtualname__


def list_cluster_compatibility(profile=None):
    """List cluster compatibility.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_compat.list_cluster_compatibility

    """
    return c.list_cluster_compatibility(__opts__, profile=profile)


def list_dvs_compatibility(cluster_id, profile=None):
    """List dvs compatibility.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_compat.list_dvs_compatibility <cluster_id>

    """
    return c.list_dvs_compatibility(__opts__, cluster_id, profile=profile)


def list_edge_cluster_compatibility(cluster_id, distributed_switch, profile=None):
    """List edge cluster compatibility.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_compat.list_edge_cluster_compatibility <cluster_id> <distributed_switch>

    """
    return c.list_edge_cluster_compatibility(
        __opts__, cluster_id, distributed_switch, profile=profile
    )


def get_cluster_size_info(profile=None):
    """Get cluster size info.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_supervisor_compat.get_cluster_size_info

    """
    return c.get_cluster_size_info(__opts__, profile=profile)
