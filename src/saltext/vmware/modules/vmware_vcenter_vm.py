"""Execution module for vCenter VMs."""

from saltext.vmware.clients import vcenter_vm as r

__virtualname__ = "vmware_vcenter_vm"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List VMs known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm.list_

    """
    return r.list_(__opts__, profile=profile)


def get(vm, profile=None):
    """Return details for a single VM by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm.get <vm>

    """
    return r.get(__opts__, vm, profile=profile)


def power_on(vm, profile=None):
    """Power on a VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm.power_on <vm>

    """
    return r.power_on(__opts__, vm, profile=profile)


def power_off(vm, profile=None):
    """Power off a VM (hard stop).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm.power_off <vm>

    """
    return r.power_off(__opts__, vm, profile=profile)


def reset(vm, profile=None):
    """Reset a VM (hard reset).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_vm.reset <vm>

    """
    return r.reset(__opts__, vm, profile=profile)
