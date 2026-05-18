"""Execution module for VM power lifecycle (A4)."""

from saltext.vcf.clients import vim_vm_power as c
from saltext.vcf.clients import vim_vm_tools as t

__virtualname__ = "vcf_vim_vm_power"


def __virtual__():
    return __virtualname__


# Power


def get_power_state(vm, profile=None):
    """Return ``poweredOn`` / ``poweredOff`` / ``suspended``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.get_power_state <vm-name-or-moid>
    """
    return c.get_power_state(__opts__, vm, profile=profile)


def power_on(vm, host=None, profile=None):
    """Hard power-on.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.power_on <vm>
    """
    return c.power_on(__opts__, vm, host=host, profile=profile)


def power_off(vm, profile=None):
    """Hard power-off.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.power_off <vm>
    """
    return c.power_off(__opts__, vm, profile=profile)


def shutdown_guest(vm, profile=None):
    """Graceful ACPI shutdown via VMware Tools.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.shutdown_guest <vm>
    """
    return c.shutdown_guest(__opts__, vm, profile=profile)


def reboot_guest(vm, profile=None):
    """Graceful reboot via VMware Tools.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.reboot_guest <vm>
    """
    return c.reboot_guest(__opts__, vm, profile=profile)


def standby_guest(vm, profile=None):
    """Standby/suspend via VMware Tools.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.standby_guest <vm>
    """
    return c.standby_guest(__opts__, vm, profile=profile)


def reset(vm, profile=None):
    """Hard reset.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.reset <vm>
    """
    return c.reset(__opts__, vm, profile=profile)


def suspend(vm, profile=None):
    """Suspend to disk.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.suspend <vm>
    """
    return c.suspend(__opts__, vm, profile=profile)


# Tools


def get_tools_status(vm, profile=None):
    """Return VMware Tools status snapshot.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.get_tools_status <vm>
    """
    return t.get_tools_status(__opts__, vm, profile=profile)


def upgrade_tools(vm, installer_options="", profile=None):
    """Upgrade VMware Tools in-guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.upgrade_tools <vm>
    """
    return t.upgrade_tools(__opts__, vm, installer_options=installer_options, profile=profile)


def mount_tools_installer(vm, profile=None):
    """Attach the VMware Tools installer CD-ROM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.mount_tools_installer <vm>
    """
    return t.mount_tools_installer(__opts__, vm, profile=profile)


def unmount_tools_installer(vm, profile=None):
    """Detach the VMware Tools installer CD-ROM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_power.unmount_tools_installer <vm>
    """
    return t.unmount_tools_installer(__opts__, vm, profile=profile)
