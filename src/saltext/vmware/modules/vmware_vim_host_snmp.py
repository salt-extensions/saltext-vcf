"""Execution module for ESXi SNMP agent config."""

from saltext.vmware.clients import vim_host_snmp as c

__virtualname__ = "vmware_vim_host_snmp"


def __virtual__():
    return __virtualname__


def get(host, profile=None):
    """Return SNMP config for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_snmp.get <host>
    """
    return c.get(__opts__, host, profile=profile)


def set_(
    host,
    enabled=None,
    port=None,
    read_only_communities=None,
    trap_targets=None,
    profile=None,
):
    """Reconfigure the SNMP agent on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_snmp.set_ <host> enabled=True
    """
    return c.set_(
        __opts__,
        host,
        enabled=enabled,
        port=port,
        read_only_communities=read_only_communities,
        trap_targets=trap_targets,
        profile=profile,
    )
