"""Execution module for ESXi TCP/IP stack config."""

from saltext.vcf.clients import vim_host_tcpip as c

__virtualname__ = "vcf_vim_host_tcpip"


def __virtual__():
    return __virtualname__


def list_(host, profile=None):
    """List TCP/IP stack instances on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_tcpip.list_ <host>
    """
    return c.list_(__opts__, host, profile=profile)


def get(host, stack_key, profile=None):
    """Return one TCP/IP stack by key.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_tcpip.get <host> defaultTcpipStack
    """
    return c.get(__opts__, host, stack_key, profile=profile)


def update(
    host,
    stack_key,
    dns_servers=None,
    dns_search_domains=None,
    profile=None,
):
    """Update DNS on a named TCP/IP stack.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_tcpip.update <host> defaultTcpipStack dns_servers='[10.0.0.1]'
    """
    return c.update(
        __opts__,
        host,
        stack_key,
        dns_servers=dns_servers,
        dns_search_domains=dns_search_domains,
        profile=profile,
    )
