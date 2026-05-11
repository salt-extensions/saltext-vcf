"""Execution module for VCF Operations appliance/node deployment status + applications."""

from saltext.vmware.clients import vcfops_deployment as c

__virtualname__ = "vmware_vcfops_deployment"


def __virtual__():
    return __virtualname__


def node_status(profile=None):
    """Node status.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_deployment.node_status

    """
    return c.node_status(__opts__, profile=profile)


def healthy(profile=None):
    """Return True when the Ops node reports an ONLINE status.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_deployment.healthy

    """
    status = c.node_status(__opts__, profile=profile)
    if isinstance(status, dict):
        return status.get("status") == "ONLINE"
    return False


def applications_list(page=0, page_size=1000):
    """Applications list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_deployment.applications_list <page> <page_size>

    """
    return c.applications_list(__opts__, page=page, page_size=page_size)


def applications_get(app_id):
    """Applications get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_deployment.applications_get <app_id>

    """
    return c.applications_get(__opts__, app_id)
