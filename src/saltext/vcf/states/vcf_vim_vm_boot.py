"""State module for VM boot options.

Idempotent wrapper over :mod:`saltext.vcf.clients.vim_vm_boot` — the
``vmware_vm.set_boot_manager`` parity state. Computes a drift dict
before applying so ``changes`` reports exactly which boot fields moved.
"""

from saltext.vcf.clients import vim_vm_boot as c

__virtualname__ = "vcf_vim_vm_boot"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def boot_manager(
    name,
    boot_order=None,
    delay=None,
    enter_bios_setup=None,
    retry_enabled=None,
    retry_delay=None,
    efi_secure_boot=None,
    profile=None,
):
    """Manage the boot options of VM *name*.

    *boot_order* is a list of device-class names (``cdrom``, ``disk``,
    ``ethernet``, ``floppy``). Only provided fields are compared and
    changed.

    .. code-block:: yaml

        Set Boot Manager:
          vcf_vim_vm_boot.boot_manager:
            - name: vm-100
            - boot_order:
                - cdrom
                - disk
            - delay: 5000
            - enter_bios_setup: false
            - retry_enabled: true
            - retry_delay: 5000
            - efi_secure_boot: false
    """
    ret = _ret(name)
    current = c.get(__opts__, name, profile=profile)
    desired = {
        "order": boot_order if boot_order is not None else current["order"],
        "delay": int(delay) if delay is not None else current["delay"],
        "enter_bios_setup": (
            bool(enter_bios_setup)
            if enter_bios_setup is not None
            else current["enter_bios_setup"]
        ),
        "retry_enabled": (
            bool(retry_enabled) if retry_enabled is not None else current["retry_enabled"]
        ),
        "retry_delay": int(retry_delay) if retry_delay is not None else current["retry_delay"],
        "efi_secure_boot_enabled": (
            bool(efi_secure_boot)
            if efi_secure_boot is not None
            else current["efi_secure_boot_enabled"]
        ),
    }
    if c.compare(desired, current):
        ret["comment"] = f"Boot options of VM {name!r} already configured as desired."
        return ret
    drift = c.drift(desired, current)
    ret["changes"] = drift
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Boot options of VM {name!r} would be updated: {sorted(drift)}."
        return ret
    c.set(
        __opts__,
        name,
        order=boot_order if boot_order is not None else None,
        delay=desired["delay"] if delay is not None else None,
        enter_bios_setup=desired["enter_bios_setup"] if enter_bios_setup is not None else None,
        retry_enabled=desired["retry_enabled"] if retry_enabled is not None else None,
        retry_delay=desired["retry_delay"] if retry_delay is not None else None,
        efi_secure_boot=(
            desired["efi_secure_boot_enabled"] if efi_secure_boot is not None else None
        ),
        profile=profile,
    )
    ret["comment"] = f"Boot options of VM {name!r} updated."
    return ret
