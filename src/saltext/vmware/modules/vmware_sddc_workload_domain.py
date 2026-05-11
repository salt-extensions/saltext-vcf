"""Execution module for SDDC Manager workload domain lifecycle (T6)."""

from saltext.vmware.clients import sddc_cluster_ops as cluster_ops
from saltext.vmware.clients import sddc_domain as domain
from saltext.vmware.clients import sddc_edge_clusters as edge
from saltext.vmware.clients import sddc_license_keys as licenses
from saltext.vmware.clients import sddc_tasks as tasks

__virtualname__ = "vmware_sddc_workload_domain"


def __virtual__():
    return __virtualname__


# Domain lifecycle


def validate_domain(spec, profile=None):
    """Validate a workload domain create spec without creating anything.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.validate_domain spec='{...}'
    """
    return domain.validate(__opts__, spec, profile=profile)


def create_domain(spec, wait=False, timeout=14400, poll_interval=30, profile=None):
    """Create a workload domain. Returns the task body (or final result if *wait*).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.create_domain spec='{...}' wait=true
    """
    task = domain.create(__opts__, spec, profile=profile)
    if wait:
        return tasks.wait(
            __opts__,
            task["id"],
            timeout=timeout,
            poll_interval=poll_interval,
            profile=profile,
        )
    return task


def update_domain(domain_id, spec, wait=False, timeout=7200, profile=None):
    """Update / expand a workload domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.update_domain <domain-id> spec='{...}'
    """
    task = domain.update(__opts__, domain_id, spec, profile=profile)
    if wait and isinstance(task, dict) and "id" in task:
        return tasks.wait(__opts__, task["id"], timeout=timeout, profile=profile)
    return task


def delete_domain(domain_id, wait=False, timeout=7200, profile=None):
    """Delete a workload domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.delete_domain <domain-id>
    """
    task = domain.delete(__opts__, domain_id, profile=profile)
    if wait and isinstance(task, dict) and "id" in task:
        return tasks.wait(__opts__, task["id"], timeout=timeout, profile=profile)
    return task


def list_endpoints(domain_id, profile=None):
    """List management endpoints (vCenter, NSX, ...) for *domain_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.list_endpoints <domain-id>
    """
    return domain.list_endpoints(__opts__, domain_id, profile=profile)


# Cluster expand/shrink


def expand_cluster(cluster_id, host_specs, wait=False, timeout=3600, profile=None):
    """Add hosts to a cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.expand_cluster <cluster-id> host_specs='[{...}]'
    """
    task = cluster_ops.expand(__opts__, cluster_id, host_specs, profile=profile)
    if wait and isinstance(task, dict) and "id" in task:
        return tasks.wait(__opts__, task["id"], timeout=timeout, profile=profile)
    return task


def shrink_cluster(cluster_id, host_ids, force=False, wait=False, timeout=3600, profile=None):
    """Remove hosts from a cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.shrink_cluster <cluster-id> host_ids='["...","..."]'
    """
    task = cluster_ops.shrink(__opts__, cluster_id, host_ids, force=force, profile=profile)
    if wait and isinstance(task, dict) and "id" in task:
        return tasks.wait(__opts__, task["id"], timeout=timeout, profile=profile)
    return task


# Edge clusters


def list_edge_clusters(profile=None):
    """List NSX edge clusters known to SDDC Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.list_edge_clusters
    """
    return edge.list_(__opts__, profile=profile)


def deploy_edge_cluster(spec, wait=False, timeout=7200, profile=None):
    """Deploy an NSX edge cluster via SDDC Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.deploy_edge_cluster spec='{...}'
    """
    task = edge.create(__opts__, spec, profile=profile)
    if wait and isinstance(task, dict) and "id" in task:
        return tasks.wait(__opts__, task["id"], timeout=timeout, profile=profile)
    return task


# License keys


def add_license_key(key, product_type, description="", profile=None):
    """Register a license key with SDDC Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.add_license_key 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX' VCENTER
    """
    return licenses.add(__opts__, key, product_type, description=description, profile=profile)


def list_license_keys(profile=None):
    """List registered license keys.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.list_license_keys
    """
    return licenses.list_(__opts__, profile=profile)


def licensing_info(profile=None):
    """Return licensing limits + allocation summary.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.licensing_info
    """
    return licenses.licensing_info(__opts__, profile=profile)


# Task polling


def task_wait(task_id, timeout=3600, poll_interval=10, profile=None):
    """Block until *task_id* reaches terminal status.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.task_wait <task-id> timeout=7200
    """
    return tasks.wait(
        __opts__, task_id, timeout=timeout, poll_interval=poll_interval, profile=profile
    )


def task_get(task_id, profile=None):
    """Return task status.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.task_get <task-id>
    """
    return tasks.get(__opts__, task_id, profile=profile)


def task_retry(task_id, profile=None):
    """Retry a Failed task.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_workload_domain.task_retry <task-id>
    """
    return tasks.retry(__opts__, task_id, profile=profile)
