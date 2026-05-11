"""Execution module for vSphere Distributed Virtual Switches (SOAP)."""

from saltext.vmware.clients import vim_dvs as c

__virtualname__ = "vmware_vim_dvs"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List every VDS.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.list_
    """
    return c.list_(__opts__, profile=profile)


def get(dvs, profile=None):
    """Return one VDS by name or moid.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.get prod-dvs
    """
    return c.get(__opts__, dvs, profile=profile)


def get_or_none(dvs, profile=None):
    """Return one VDS or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.get_or_none prod-dvs
    """
    return c.get_or_none(__opts__, dvs, profile=profile)


def create(
    name,
    datacenter,
    version=None,
    num_uplinks=4,
    max_mtu=1500,
    description="",
    profile=None,
):
    """Create a VDS in *datacenter*'s networkFolder.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.create prod-dvs Datacenter num_uplinks=4 max_mtu=9000
    """
    return c.create(
        __opts__,
        name,
        datacenter,
        version=version,
        num_uplinks=num_uplinks,
        max_mtu=max_mtu,
        description=description,
        profile=profile,
    )


def reconfigure(dvs, max_mtu=None, description=None, profile=None):
    """Update VDS config fields.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.reconfigure prod-dvs max_mtu=9000
    """
    return c.reconfigure(__opts__, dvs, max_mtu=max_mtu, description=description, profile=profile)


def delete(dvs, profile=None):
    """Delete the VDS.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.delete prod-dvs
    """
    return c.delete(__opts__, dvs, profile=profile)


def add_host(dvs, host, pnic_devices=None, profile=None):
    """Attach a host to the VDS, optionally pinning pNICs to uplinks.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.add_host prod-dvs esxi-01 pnic_devices='["vmnic0","vmnic1"]'
    """
    return c.add_host(__opts__, dvs, host, pnic_devices=pnic_devices, profile=profile)


def remove_host(dvs, host, profile=None):
    """Detach a host from the VDS.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_dvs.remove_host prod-dvs esxi-01
    """
    return c.remove_host(__opts__, dvs, host, profile=profile)
