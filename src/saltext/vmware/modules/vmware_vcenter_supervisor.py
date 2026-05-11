"""Execution module for vCenter Supervisor / VKS."""

from saltext.vmware.clients import vcenter_supervisor as c

__virtualname__ = "vmware_vcenter_supervisor"


def __virtual__():
    return __virtualname__


def list_clusters(profile=None):
    """List clusters.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.list_clusters

    """
    return c.list_clusters(__opts__, profile=profile)


def get_cluster(cluster_id, profile=None):
    """Get cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.get_cluster <cluster_id>

    """
    return c.get_cluster(__opts__, cluster_id, profile=profile)


def list_compatibility(profile=None):
    """List compatibility.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.list_compatibility

    """
    return c.list_compatibility(__opts__, profile=profile)


def enable_cluster(cluster_id, enable_spec, profile=None):
    """Enable cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.enable_cluster <cluster_id> <enable_spec>

    """
    return c.enable_cluster(__opts__, cluster_id, enable_spec, profile=profile)


def disable_cluster(cluster_id, profile=None):
    """Disable cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.disable_cluster <cluster_id>

    """
    return c.disable_cluster(__opts__, cluster_id, profile=profile)


def list_namespaces(profile=None):
    """List namespaces.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.list_namespaces

    """
    return c.list_namespaces(__opts__, profile=profile)


def get_namespace(namespace_id, profile=None):
    """Get namespace.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.get_namespace <namespace_id>

    """
    return c.get_namespace(__opts__, namespace_id, profile=profile)


def create_namespace(namespace_spec, profile=None):
    """Create namespace.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.create_namespace <namespace_spec>

    """
    return c.create_namespace(__opts__, namespace_spec, profile=profile)


def delete_namespace(namespace_id, profile=None):
    """Delete namespace.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor.delete_namespace <namespace_id>

    """
    return c.delete_namespace(__opts__, namespace_id, profile=profile)
