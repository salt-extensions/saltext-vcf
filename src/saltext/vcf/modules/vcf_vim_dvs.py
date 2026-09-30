"""Execution module for vSphere Distributed Virtual Switches (SOAP)."""

from saltext.vcf.clients import vim_dvs as c

__virtualname__ = "vcf_vim_dvs"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List every VDS.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.list_
    """
    return c.list_(__opts__, profile=profile)


def get(dvs, profile=None):
    """Return one VDS by name or moid.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.get prod-dvs
    """
    return c.get(__opts__, dvs, profile=profile)


def get_or_none(dvs, profile=None):
    """Return one VDS or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.get_or_none prod-dvs
    """
    return c.get_or_none(__opts__, dvs, profile=profile)


def create(
    name,
    datacenter,
    version=None,
    num_uplinks=4,
    max_mtu=1500,
    description="",
    uplink_prefix="uplink",
    discovery_protocol=None,
    discovery_operation=None,
    multicast_filtering_mode=None,
    contact_name=None,
    contact_description=None,
    network_promiscuous=None,
    network_mac_changes=None,
    network_forged_transmits=None,
    health_check_vlan_mtu=None,
    health_check_vlan_mtu_interval=None,
    health_check_teaming_failover=None,
    health_check_teaming_failover_interval=None,
    profile=None,
):
    """Create a VDS in *datacenter*'s networkFolder (full spec surface).

    *discovery_protocol*: ``cdp`` | ``lldp`` | ``disabled``;
    *multicast_filtering_mode*: ``basic`` | ``snooping``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.create prod-dvs Datacenter num_uplinks=4 max_mtu=9000
    """
    return c.create(
        __opts__,
        name,
        datacenter,
        version=version,
        num_uplinks=num_uplinks,
        max_mtu=max_mtu,
        description=description,
        uplink_prefix=uplink_prefix,
        discovery_protocol=discovery_protocol,
        discovery_operation=discovery_operation,
        multicast_filtering_mode=multicast_filtering_mode,
        contact_name=contact_name,
        contact_description=contact_description,
        network_promiscuous=network_promiscuous,
        network_mac_changes=network_mac_changes,
        network_forged_transmits=network_forged_transmits,
        health_check_vlan_mtu=health_check_vlan_mtu,
        health_check_vlan_mtu_interval=health_check_vlan_mtu_interval,
        health_check_teaming_failover=health_check_teaming_failover,
        health_check_teaming_failover_interval=health_check_teaming_failover_interval,
        profile=profile,
    )


def reconfigure(
    dvs,
    max_mtu=None,
    description=None,
    uplink_prefix=None,
    num_uplinks=None,
    discovery_protocol=None,
    discovery_operation=None,
    multicast_filtering_mode=None,
    contact_name=None,
    contact_description=None,
    network_promiscuous=None,
    network_mac_changes=None,
    network_forged_transmits=None,
    health_check_vlan_mtu=None,
    health_check_vlan_mtu_interval=None,
    health_check_teaming_failover=None,
    health_check_teaming_failover_interval=None,
    version=None,
    profile=None,
):
    """Update VDS config fields (full spec surface).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.reconfigure prod-dvs max_mtu=9000
    """
    return c.reconfigure(
        __opts__,
        dvs,
        max_mtu=max_mtu,
        description=description,
        uplink_prefix=uplink_prefix,
        num_uplinks=num_uplinks,
        discovery_protocol=discovery_protocol,
        discovery_operation=discovery_operation,
        multicast_filtering_mode=multicast_filtering_mode,
        contact_name=contact_name,
        contact_description=contact_description,
        network_promiscuous=network_promiscuous,
        network_mac_changes=network_mac_changes,
        network_forged_transmits=network_forged_transmits,
        health_check_vlan_mtu=health_check_vlan_mtu,
        health_check_vlan_mtu_interval=health_check_vlan_mtu_interval,
        health_check_teaming_failover=health_check_teaming_failover,
        health_check_teaming_failover_interval=health_check_teaming_failover_interval,
        version=version,
        profile=profile,
    )


def delete(dvs, profile=None):
    """Delete the VDS.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.delete prod-dvs
    """
    return c.delete(__opts__, dvs, profile=profile)


def add_host(dvs, host, pnic_devices=None, profile=None):
    """Attach a host to the VDS, optionally pinning pNICs to uplinks.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.add_host prod-dvs esxi-01 pnic_devices='["vmnic0","vmnic1"]'
    """
    return c.add_host(__opts__, dvs, host, pnic_devices=pnic_devices, profile=profile)


def remove_host(dvs, host, profile=None):
    """Detach a host from the VDS.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs.remove_host prod-dvs esxi-01
    """
    return c.remove_host(__opts__, dvs, host, profile=profile)
