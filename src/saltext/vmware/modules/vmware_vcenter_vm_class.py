"""Execution module for vCenter Supervisor VM Classes (VKS)."""

from saltext.vmware.clients import vcenter_vm_class as c

__virtualname__ = "vmware_vcenter_vm_class"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm_class.list_

    """
    return c.list_(__opts__, profile=profile)


def get(class_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm_class.get <class_id>

    """
    return c.get(__opts__, class_id, profile=profile)


def create(class_spec, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm_class.create <class_spec>

    """
    return c.create(__opts__, class_spec, profile=profile)


def update(class_id, class_spec, profile=None):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm_class.update <class_id> <class_spec>

    """
    return c.update(__opts__, class_id, class_spec, profile=profile)


def delete(class_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm_class.delete <class_id>

    """
    return c.delete(__opts__, class_id, profile=profile)
