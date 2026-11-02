"""Execution module for ESXi host lifecycle, power state and info (SOAP)."""

from saltext.vcf.clients import vim_host as c

__virtualname__ = "vcf_vim_host"


def __virtual__():
    return __virtualname__


def connection_state(host, profile=None):
    """Return the host's current vCenter connection state.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.connection_state esxi-01
    """
    return c.connection_state(__opts__, host, profile=profile)


def reconnect(host, profile=None):
    """Reconnect a disconnected ESXi host to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.reconnect esxi-01
    """
    return c.reconnect(__opts__, host, profile=profile)


def disconnect(host, profile=None):
    """Disconnect an ESXi host from vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.disconnect esxi-01
    """
    return c.disconnect(__opts__, host, profile=profile)


def remove(host, profile=None):
    """Remove an ESXi host from vCenter inventory.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.remove esxi-01
    """
    return c.destroy(__opts__, host, profile=profile)


def move(host, cluster, profile=None):
    """Move an ESXi host into *cluster* (same datacenter required).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.move esxi-01 cluster=target-cl
    """
    return c.move(__opts__, host, cluster, profile=profile)


def add(
    host,
    root_user,
    password,
    cluster,
    datacenter,
    verify_host_cert=False,
    connect=True,
    profile=None,
):
    """Add a bare ESXi host to vCenter under *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.add 10.0.0.51 root secret cluster=cl-1 datacenter=dc-1 verify_host_cert=false
    """
    return c.add(
        __opts__,
        host,
        root_user,
        password,
        cluster,
        datacenter,
        verify_host_cert=verify_host_cert,
        connect=connect,
        profile=profile,
    )


def power_state(host, state, timeout=600, force=True, profile=None):
    """Transition host power state: ``reboot`` | ``shutdown`` | ``standby`` | ``poweron``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.power_state esxi-01 state=reboot
    """
    return c.power_state(__opts__, host, state, timeout=timeout, force=force, profile=profile)


def capabilities(host, profile=None):
    """Return the host's ``HostCapability`` attributes as a snake_case dict.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.capabilities esxi-01
    """
    return c.capabilities(__opts__, host, profile=profile)


def info(host, key=None, default="", delimiter=":", profile=None):
    """Return the composed per-host info dict (or one traversed *key*).

    *key* supports nested traversal (``vsan:health``) with grains.get
    semantics, returning *default* when absent.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host.info esxi-01 key=vsan:health
    """
    return c.info(__opts__, host, key=key, default=default, delimiter=delimiter, profile=profile)
