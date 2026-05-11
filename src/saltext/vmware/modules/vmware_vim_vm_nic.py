"""Execution module for VM NIC lifecycle (SOAP)."""

from saltext.vmware.clients import vim_vm_nic as c

__virtualname__ = "vmware_vim_vm_nic"


def __virtual__():
    return __virtualname__


def list_(vm, profile=None):
    """List every NIC on *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_nic.list_ vm-100
    """
    return c.list_(__opts__, vm, profile=profile)


def add(
    vm,
    nic_type="vmxnet3",
    network_moid=None,
    portgroup_key=None,
    dvs_uuid=None,
    mac_address=None,
    start_connected=True,
    profile=None,
):
    """Add a new NIC.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_nic.add vm-100 nic_type=vmxnet3 network_moid=network-12
    """
    return c.add(
        __opts__,
        vm,
        nic_type=nic_type,
        network_moid=network_moid,
        portgroup_key=portgroup_key,
        dvs_uuid=dvs_uuid,
        mac_address=mac_address,
        start_connected=start_connected,
        profile=profile,
    )


def update_backing(
    vm,
    nic_key,
    network_moid=None,
    portgroup_key=None,
    dvs_uuid=None,
    profile=None,
):
    """Reattach an existing NIC to a different network.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_nic.update_backing vm-100 4000 network_moid=network-42
    """
    return c.update_backing(
        __opts__,
        vm,
        nic_key,
        network_moid=network_moid,
        portgroup_key=portgroup_key,
        dvs_uuid=dvs_uuid,
        profile=profile,
    )


def set_connected(vm, nic_key, connected, profile=None):
    """Hot-toggle a NIC's connected state.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_nic.set_connected vm-100 4000 true
    """
    return c.set_connected(__opts__, vm, nic_key, connected, profile=profile)


def remove(vm, nic_key, profile=None):
    """Remove a NIC by its device key.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_nic.remove vm-100 4000
    """
    return c.remove(__opts__, vm, nic_key, profile=profile)
