"""Execution module for ESXi PCI passthrough (SOAP)."""

from saltext.vmware.clients import vim_host_passthrough as c

__virtualname__ = "vmware_vim_host_passthrough"


def __virtual__():
    return __virtualname__


def list_(host, profile=None):
    """List PCI passthrough devices on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_passthrough.list_ <host>

    """
    return c.list_(__opts__, host, profile=profile)


def refresh(host, profile=None):
    """Force the host to re-scan its PCI inventory.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_passthrough.refresh <host>

    """
    return c.refresh(__opts__, host, profile=profile)


def set_enabled(host, pci_id, enabled, profile=None):
    """Toggle passthrough on a single PCI device. Requires reboot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_passthrough.set_enabled <host> <pci_id> <enabled>

    """
    return c.set_enabled(__opts__, host, pci_id, enabled, profile=profile)
