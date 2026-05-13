"""Execution module for ESXi host DNS config (SOAP)."""

from saltext.vmware.clients import vim_host_dns as c

__virtualname__ = "vmware_vim_host_dns"


def __virtual__():
    return __virtualname__


def get(host, profile=None):
    """Return ``{dhcp, hostname, domain_name, servers, search_domains, virtual_nic}``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_dns.get <host>

    """
    return c.get(__opts__, host, profile=profile)


def set_(
    host,
    dhcp=None,
    hostname=None,
    domain_name=None,
    servers=None,
    search_domains=None,
    virtual_nic=None,
    profile=None,
):
    """Update host DNS config. None args leave existing values alone.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_dns.set_ <host> servers='[10.0.0.1]'

    """
    return c.set_(
        __opts__,
        host,
        dhcp=dhcp,
        hostname=hostname,
        domain_name=domain_name,
        servers=servers,
        search_domains=search_domains,
        virtual_nic=virtual_nic,
        profile=profile,
    )
