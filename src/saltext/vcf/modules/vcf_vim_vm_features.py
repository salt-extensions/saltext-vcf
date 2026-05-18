"""Execution module for VM advanced features + hardware version upgrade (A6)."""

from saltext.vcf.clients import vim_vm_features as f

__virtualname__ = "vcf_vim_vm_features"


def __virtual__():
    return __virtualname__


def get_features(vm, profile=None):
    """Return a snapshot of advanced VM toggles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_features.get_features <vm>
    """
    return f.get_features(__opts__, vm, profile=profile)


def set_features(
    vm,
    cpu_hot_add=None,
    memory_hot_add=None,
    nested_hv=None,
    latency_sensitivity=None,
    tools_sync_time_with_host=None,
    firmware=None,
    boot_delay=None,
    enter_bios_setup=None,
    efi_secure_boot=None,
    profile=None,
):
    """Update advanced VM toggles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_features.set_features <vm> cpu_hot_add=True nested_hv=True
    """
    return f.set_features(
        __opts__,
        vm,
        cpu_hot_add=cpu_hot_add,
        memory_hot_add=memory_hot_add,
        nested_hv=nested_hv,
        latency_sensitivity=latency_sensitivity,
        tools_sync_time_with_host=tools_sync_time_with_host,
        firmware=firmware,
        boot_delay=boot_delay,
        enter_bios_setup=enter_bios_setup,
        efi_secure_boot=efi_secure_boot,
        profile=profile,
    )


def upgrade_hardware(vm, version=None, profile=None):
    """Upgrade VM hardware version.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_features.upgrade_hardware <vm> version=vmx-21
    """
    return f.upgrade_hardware(__opts__, vm, version=version, profile=profile)
