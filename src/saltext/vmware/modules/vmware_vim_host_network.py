"""Execution module for standard vSwitch / port group / VMkernel (SOAP)."""

from saltext.vmware.clients import vim_host_network as c

__virtualname__ = "vmware_vim_host_network"


def __virtual__():
    return __virtualname__


# vSwitches


def vswitch_list(host, profile=None):
    """List standard vSwitches on the host.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vswitch_list esxi-01
    """
    return c.vswitch_list(__opts__, host, profile=profile)


def vswitch_get(host, name, profile=None):
    """Return one vSwitch.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vswitch_get esxi-01 vSwitch0
    """
    return c.vswitch_get(__opts__, host, name, profile=profile)


def vswitch_get_or_none(host, name, profile=None):
    """Return one vSwitch or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vswitch_get_or_none esxi-01 vSwitch1
    """
    return c.vswitch_get_or_none(__opts__, host, name, profile=profile)


def vswitch_add(host, name, num_ports=128, mtu=1500, pnic_devices=None, profile=None):
    """Add a standard vSwitch.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vswitch_add esxi-01 vSwitch1 pnic_devices='["vmnic1"]'
    """
    return c.vswitch_add(
        __opts__,
        host,
        name,
        num_ports=num_ports,
        mtu=mtu,
        pnic_devices=pnic_devices,
        profile=profile,
    )


def vswitch_update(host, name, num_ports=None, mtu=None, pnic_devices=None, profile=None):
    """Update a vSwitch.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vswitch_update esxi-01 vSwitch1 mtu=9000
    """
    return c.vswitch_update(
        __opts__,
        host,
        name,
        num_ports=num_ports,
        mtu=mtu,
        pnic_devices=pnic_devices,
        profile=profile,
    )


def vswitch_remove(host, name, profile=None):
    """Remove a vSwitch.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vswitch_remove esxi-01 vSwitch1
    """
    return c.vswitch_remove(__opts__, host, name, profile=profile)


# Port groups


def portgroup_list(host, profile=None):
    """List standard port groups.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.portgroup_list esxi-01
    """
    return c.portgroup_list(__opts__, host, profile=profile)


def portgroup_get(host, name, profile=None):
    """Return one port group.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.portgroup_get esxi-01 Management
    """
    return c.portgroup_get(__opts__, host, name, profile=profile)


def portgroup_get_or_none(host, name, profile=None):
    """Return one port group or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.portgroup_get_or_none esxi-01 NotThere
    """
    return c.portgroup_get_or_none(__opts__, host, name, profile=profile)


def portgroup_add(host, name, vswitch, vlan_id=0, profile=None):
    """Add a standard port group.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.portgroup_add esxi-01 Mgmt vSwitch0 vlan_id=10
    """
    return c.portgroup_add(__opts__, host, name, vswitch, vlan_id=vlan_id, profile=profile)


def portgroup_update(host, name, vlan_id=None, vswitch=None, profile=None):
    """Update a standard port group.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.portgroup_update esxi-01 Mgmt vlan_id=20
    """
    return c.portgroup_update(
        __opts__, host, name, vlan_id=vlan_id, vswitch=vswitch, profile=profile
    )


def portgroup_remove(host, name, profile=None):
    """Remove a standard port group.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.portgroup_remove esxi-01 Mgmt
    """
    return c.portgroup_remove(__opts__, host, name, profile=profile)


# VMkernel


def vmkernel_list(host, profile=None):
    """List VMkernel adapters.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_list esxi-01
    """
    return c.vmkernel_list(__opts__, host, profile=profile)


def vmkernel_get(host, device, profile=None):
    """Return one VMkernel adapter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_get esxi-01 vmk0
    """
    return c.vmkernel_get(__opts__, host, device, profile=profile)


def vmkernel_get_or_none(host, device, profile=None):
    """Return one VMkernel adapter or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_get_or_none esxi-01 vmk99
    """
    return c.vmkernel_get_or_none(__opts__, host, device, profile=profile)


def vmkernel_add(
    host,
    portgroup,
    dhcp=False,
    ip_address=None,
    subnet_mask=None,
    mtu=1500,
    mac_address=None,
    nic_types=None,
    profile=None,
):
    """Add a VMkernel adapter; returns the new device name (e.g. ``vmk1``).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_add esxi-01 vMotion ip_address=10.0.0.5 subnet_mask=255.255.255.0 nic_types='["vmotion"]'
    """
    return c.vmkernel_add(
        __opts__,
        host,
        portgroup,
        dhcp=dhcp,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        mtu=mtu,
        mac_address=mac_address,
        nic_types=nic_types,
        profile=profile,
    )


def vmkernel_update(
    host,
    device,
    dhcp=None,
    ip_address=None,
    subnet_mask=None,
    mtu=None,
    profile=None,
):
    """Update a VMkernel adapter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_update esxi-01 vmk1 mtu=9000
    """
    return c.vmkernel_update(
        __opts__,
        host,
        device,
        dhcp=dhcp,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        mtu=mtu,
        profile=profile,
    )


def vmkernel_remove(host, device, profile=None):
    """Remove a VMkernel adapter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_remove esxi-01 vmk1
    """
    return c.vmkernel_remove(__opts__, host, device, profile=profile)


def vmkernel_set_traffic_types(host, device, nic_types, profile=None):
    """Replace the traffic-type list on a VMkernel adapter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.vmkernel_set_traffic_types esxi-01 vmk1 '["vmotion","provisioning"]'
    """
    return c.vmkernel_set_traffic_types(__opts__, host, device, nic_types, profile=profile)


def physical_nic_list(host, profile=None):
    """List physical NICs (pNICs) on the host.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_network.physical_nic_list esxi-01
    """
    return c.physical_nic_list(__opts__, host, profile=profile)
