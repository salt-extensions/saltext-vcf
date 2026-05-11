"""Execution module for vCenter Supervisor Services catalog (VKS)."""

from saltext.vmware.clients import vcenter_supervisor_service as c

__virtualname__ = "vmware_vcenter_supervisor_service"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.list_

    """
    return c.list_(__opts__, profile=profile)


def get(service_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.get <service_id>

    """
    return c.get(__opts__, service_id, profile=profile)


def list_versions(service_id, profile=None):
    """List versions.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.list_versions <service_id>

    """
    return c.list_versions(__opts__, service_id, profile=profile)


def get_version(service_id, version, profile=None):
    """Get version.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.get_version <service_id> <version>

    """
    return c.get_version(__opts__, service_id, version, profile=profile)


def create(service_spec, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.create <service_spec>

    """
    return c.create(__opts__, service_spec, profile=profile)


def activate(service_id, profile=None):
    """Activate.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.activate <service_id>

    """
    return c.activate(__opts__, service_id, profile=profile)


def deactivate(service_id, profile=None):
    """Deactivate.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.deactivate <service_id>

    """
    return c.deactivate(__opts__, service_id, profile=profile)


def delete(service_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_supervisor_service.delete <service_id>

    """
    return c.delete(__opts__, service_id, profile=profile)
