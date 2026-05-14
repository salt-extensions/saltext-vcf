"""Execution module for niche VM virtual devices (vTPM, vGPU, video, serial)."""

from saltext.vmware.clients import vim_vm_devices as c

__virtualname__ = "vmware_vim_vm_devices"


def __virtual__():
    return __virtualname__


# vTPM ----------------------------------------------------------------------


def tpm_list(vm, profile=None):
    """List vTPM devices on *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.tpm_list <vm>
    """
    return c.tpm_list(__opts__, vm, profile=profile)


def tpm_add(vm, profile=None):
    """Add a vTPM 2.0 device to *vm* (must be powered off).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.tpm_add <vm>
    """
    return c.tpm_add(__opts__, vm, profile=profile)


def tpm_remove(vm, profile=None):
    """Remove the vTPM device from *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.tpm_remove <vm>
    """
    return c.tpm_remove(__opts__, vm, profile=profile)


# vGPU ----------------------------------------------------------------------


def vgpu_list(vm, profile=None):
    """List vGPU devices on *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.vgpu_list <vm>
    """
    return c.vgpu_list(__opts__, vm, profile=profile)


def vgpu_add(vm, profile_name, profile=None):
    """Attach a vGPU device with *profile_name* (e.g. grid_a100d-8c).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.vgpu_add <vm> grid_a100d-8c
    """
    return c.vgpu_add(__opts__, vm, profile_name, profile=profile)


def vgpu_remove(vm, profile_name=None, profile=None):
    """Remove a vGPU device. If *profile_name* given, only that one.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.vgpu_remove <vm>
    """
    return c.vgpu_remove(__opts__, vm, profile_name=profile_name, profile=profile)


# Video card ---------------------------------------------------------------


def video_get(vm, profile=None):
    """Return the VM's video card config.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.video_get <vm>
    """
    return c.video_get(__opts__, vm, profile=profile)


def video_update(
    vm,
    video_ram_size_kb=None,
    num_displays=None,
    enable_3d_support=None,
    graphics_memory_size_kb=None,
    profile=None,
):
    """Update the VM's video card.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.video_update <vm> num_displays=2
    """
    return c.video_update(
        __opts__,
        vm,
        video_ram_size_kb=video_ram_size_kb,
        num_displays=num_displays,
        enable_3d_support=enable_3d_support,
        graphics_memory_size_kb=graphics_memory_size_kb,
        profile=profile,
    )


# Serial port --------------------------------------------------------------


def serial_list(vm, profile=None):
    """List serial ports on *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.serial_list <vm>
    """
    return c.serial_list(__opts__, vm, profile=profile)


def serial_add(
    vm,
    backing="network",
    uri=None,
    direction="server",
    file_path=None,
    profile=None,
):
    """Add a serial port.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.serial_add <vm> backing=network uri=tcp://0.0.0.0:9000
    """
    return c.serial_add(
        __opts__,
        vm,
        backing=backing,
        uri=uri,
        direction=direction,
        file_path=file_path,
        profile=profile,
    )


def serial_remove(vm, key=None, profile=None):
    """Remove a serial port by *key*, or the first one if key is None.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_devices.serial_remove <vm>
    """
    return c.serial_remove(__opts__, vm, key=key, profile=profile)
