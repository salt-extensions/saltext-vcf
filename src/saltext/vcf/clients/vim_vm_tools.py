"""VMware Tools daemon control via SOAP."""

from saltext.vcf.clients.vim_vm import _vm


def get_tools_status(opts, vm_id_or_name, profile=None):
    """Return a snapshot of the VM's VMware Tools status.

    Keys: ``toolsStatus``, ``toolsVersionStatus``, ``toolsRunningStatus``,
    ``toolsInstallType``, ``toolsVersion``.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    guest = vm.guest
    return {
        "toolsStatus": str(guest.toolsStatus) if guest.toolsStatus else None,
        "toolsVersionStatus": getattr(guest, "toolsVersionStatus2", None),
        "toolsRunningStatus": getattr(guest, "toolsRunningStatus", None),
        "toolsInstallType": getattr(guest, "toolsInstallType", None),
        "toolsVersion": getattr(guest, "toolsVersion", None),
    }


def upgrade_tools(opts, vm_id_or_name, installer_options="", profile=None):
    """Upgrade VMware Tools in-guest. Returns task moid."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.UpgradeTools_Task(installerOptions=installer_options)
    return task._moId  # noqa: SLF001


def mount_tools_installer(opts, vm_id_or_name, profile=None):
    """Attach the VMware Tools installer CD-ROM. Synchronous."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    vm.MountToolsInstaller()
    return True


def unmount_tools_installer(opts, vm_id_or_name, profile=None):
    """Detach the VMware Tools installer CD-ROM. Synchronous."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    vm.UnmountToolsInstaller()
    return True
