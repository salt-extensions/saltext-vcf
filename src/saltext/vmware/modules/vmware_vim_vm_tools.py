"""Execution module for VMware Tools control."""

from saltext.vmware.clients import vim_vm_tools as c

__virtualname__ = "vmware_vim_vm_tools"


def __virtual__():
    return __virtualname__


def get_tools_status(vm, profile=None):
    """Return VMware Tools status snapshot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_tools.get_tools_status <vm>
    """
    return c.get_tools_status(__opts__, vm, profile=profile)


def upgrade_tools(vm, installer_options="", profile=None):
    """Upgrade VMware Tools in *vm*'s guest. Returns task moId.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_tools.upgrade_tools <vm>
    """
    return c.upgrade_tools(__opts__, vm, installer_options=installer_options, profile=profile)


def mount_tools_installer(vm, profile=None):
    """Attach the VMware Tools installer CD-ROM.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_tools.mount_tools_installer <vm>
    """
    return c.mount_tools_installer(__opts__, vm, profile=profile)


def unmount_tools_installer(vm, profile=None):
    """Detach the VMware Tools installer CD-ROM.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_tools.unmount_tools_installer <vm>
    """
    return c.unmount_tools_installer(__opts__, vm, profile=profile)
