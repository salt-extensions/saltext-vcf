"""Execution module for NSX DHCP server + relay configs."""

from saltext.vcf.clients import nsx_dhcp as c

__virtualname__ = "vcf_nsx_dhcp"


def __virtual__():
    return __virtualname__


def server_list(profile=None):
    """Server list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.server_list

    """
    return c.server_list(__opts__, profile=profile)


def server_get(server_id, profile=None):
    """Server get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.server_get <server_id>

    """
    return c.server_get(__opts__, server_id, profile=profile)


def server_create(server_id, profile=None, **spec):
    """Server create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.server_create <server_id>

    """
    return c.server_create(__opts__, server_id, profile=profile, **spec)


def server_delete(server_id, profile=None):
    """Server delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.server_delete <server_id>

    """
    return c.server_delete(__opts__, server_id, profile=profile)


def relay_list(profile=None):
    """Relay list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.relay_list

    """
    return c.relay_list(__opts__, profile=profile)


def relay_get(relay_id, profile=None):
    """Relay get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.relay_get <relay_id>

    """
    return c.relay_get(__opts__, relay_id, profile=profile)


def relay_create(relay_id, server_addresses, profile=None, **spec):
    """Relay create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.relay_create <relay_id> <server_addresses>

    """
    return c.relay_create(__opts__, relay_id, server_addresses, profile=profile, **spec)


def relay_delete(relay_id, profile=None):
    """Relay delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_dhcp.relay_delete <relay_id>

    """
    return c.relay_delete(__opts__, relay_id, profile=profile)
