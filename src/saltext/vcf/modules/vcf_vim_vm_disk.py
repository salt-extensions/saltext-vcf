"""Execution module for VM disk lifecycle (SOAP)."""

from saltext.vcf.clients import vim_vm_disk as c

__virtualname__ = "vcf_vim_vm_disk"


def __virtual__():
    return __virtualname__


def list_(vm, profile=None):
    """List every VirtualDisk on *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_disk.list_ vm-100
    """
    return c.list_(__opts__, vm, profile=profile)


def add(
    vm,
    size_gb,
    datastore_moid=None,
    controller_key=None,
    unit_number=None,
    disk_mode="persistent",
    thin=True,
    eager_scrub=False,
    profile=None,
):
    """Add a new disk to *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_disk.add vm-100 50 thin=true
    """
    return c.add(
        __opts__,
        vm,
        size_gb,
        datastore_moid=datastore_moid,
        controller_key=controller_key,
        unit_number=unit_number,
        disk_mode=disk_mode,
        thin=thin,
        eager_scrub=eager_scrub,
        profile=profile,
    )


def resize(vm, disk_key, size_gb, profile=None):
    """Resize a disk by its device key.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_disk.resize vm-100 2000 100
    """
    return c.resize(__opts__, vm, disk_key, size_gb, profile=profile)


def remove(vm, disk_key, destroy_files=False, profile=None):
    """Remove a disk by its device key.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_disk.remove vm-100 2000 destroy_files=false
    """
    return c.remove(__opts__, vm, disk_key, destroy_files=destroy_files, profile=profile)
