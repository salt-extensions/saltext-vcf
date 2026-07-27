"""Execution module for distributed port groups (SOAP)."""

from saltext.vcf.clients import vim_dvs_portgroup as c

__virtualname__ = "vcf_vim_dvs_portgroup"


def __virtual__():
    return __virtualname__


def list_(dvs, profile=None):
    """List every DPG on *dvs*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.list_ prod-dvs
    """
    return c.list_(__opts__, dvs, profile=profile)


def get(dvs, name, profile=None):
    """Return one DPG.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.get prod-dvs prod-web
    """
    return c.get(__opts__, dvs, name, profile=profile)


def get_or_none(dvs, name, profile=None):
    """Return one DPG or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.get_or_none prod-dvs prod-web
    """
    return c.get_or_none(__opts__, dvs, name, profile=profile)


def create_vlan(
    dvs,
    name,
    vlan_id=0,
    num_ports=8,
    binding="earlyBinding",
    auto_expand=True,
    promiscuous=False,
    profile=None,
):
    """Create a VLAN-backed DPG.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.create_vlan prod-dvs prod-web vlan_id=100
    """
    return c.create_vlan(
        __opts__,
        dvs,
        name,
        vlan_id=vlan_id,
        num_ports=num_ports,
        binding=binding,
        auto_expand=auto_expand,
        promiscuous=promiscuous,
        profile=profile,
    )


def create_trunk(
    dvs,
    name,
    vlan_ranges,
    num_ports=8,
    binding="earlyBinding",
    profile=None,
):
    """Create a VLAN-trunk-backed DPG.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.create_trunk prod-dvs trunk-uplink '[[100,200]]'
    """
    return c.create_trunk(
        __opts__,
        dvs,
        name,
        vlan_ranges=vlan_ranges,
        num_ports=num_ports,
        binding=binding,
        profile=profile,
    )


def reconfigure(dvs, name, vlan_id=None, num_ports=None, promiscuous=None, profile=None):
    """Update DPG config fields.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.reconfigure prod-dvs prod-web vlan_id=200
    """
    return c.reconfigure(
        __opts__,
        dvs,
        name,
        vlan_id=vlan_id,
        num_ports=num_ports,
        promiscuous=promiscuous,
        profile=profile,
    )


def delete(dvs, name, profile=None):
    """Delete a DPG.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.delete prod-dvs prod-web
    """
    return c.delete(__opts__, dvs, name, profile=profile)


def get_teaming(dvs, name, profile=None):
    """Return the current uplink teaming policy for DPG *name*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.get_teaming prod-dvs prod-web
    """
    return c.get_teaming(__opts__, dvs, name, profile=profile)


def set_teaming(
    dvs,
    name,
    policy,
    reverse_policy=None,
    notify_switches=None,
    rolling_order=None,
    check_beacon=None,
    active_uplinks=None,
    standby_uplinks=None,
    profile=None,
):
    """Set the uplink teaming / physical-failover policy on DPG *name*.

    *policy* is one of ``loadbalance_ip``, ``loadbalance_srcmac``,
    ``loadbalance_srcid``, ``failover_explicit``, ``loadbalance_loadbased``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_dvs_portgroup.set_teaming prod-dvs prod-web loadbalance_loadbased \\
            active_uplinks='["Uplink 1","Uplink 2"]'
    """
    return c.set_teaming(
        __opts__,
        dvs,
        name,
        policy=policy,
        reverse_policy=reverse_policy,
        notify_switches=notify_switches,
        rolling_order=rolling_order,
        check_beacon=check_beacon,
        active_uplinks=active_uplinks,
        standby_uplinks=standby_uplinks,
        profile=profile,
    )
