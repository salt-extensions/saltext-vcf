"""Execution module for VM boot options (order, delay, retry, secure boot)."""

from saltext.vcf.clients import vim_vm_boot as c

__virtualname__ = "vcf_vim_vm_boot"


def __virtual__():
    return __virtualname__


def get(vm, profile=None):
    """Return the VM's boot options as a dict.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_boot.get vm-100
    """
    return c.get(__opts__, vm, profile=profile)


def set(
    vm,
    order=None,
    delay=None,
    enter_bios_setup=None,
    retry_enabled=None,
    retry_delay=None,
    efi_secure_boot=None,
    profile=None,
):
    """Update VM boot options.

    *order* is a list of device-class names (``cdrom``, ``disk``,
    ``ethernet``, ``floppy``); entries without matching hardware are
    skipped. Only non-None fields are applied.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_boot.set vm-100 order='["cdrom", "disk"]' delay=5000 retry_enabled=true
    """
    return c.set(
        __opts__,
        vm,
        order=order,
        delay=delay,
        enter_bios_setup=enter_bios_setup,
        retry_enabled=retry_enabled,
        retry_delay=retry_delay,
        efi_secure_boot=efi_secure_boot,
        profile=profile,
    )
