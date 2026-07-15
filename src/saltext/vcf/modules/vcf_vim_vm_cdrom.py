"""Execution module for VM CD/DVD lifecycle (SOAP)."""

from saltext.vcf.clients import vim_vm_cdrom as c

__virtualname__ = "vcf_vim_vm_cdrom"


def __virtual__():
    return __virtualname__


def list_(vm, profile=None):
    """List every CD-ROM on *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_cdrom.list_ vm-100
    """
    return c.list_(__opts__, vm, profile=profile)


def add(
    vm,
    iso_path=None,
    datastore=None,
    controller_key=None,
    start_connected=True,
    profile=None,
):
    """Add a new CD-ROM.  With *iso_path*, backs the drive with an ISO.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_cdrom.add vm-100 iso_path='isos/foo.iso' datastore=datastore-ssd-4tb
    """
    return c.add(
        __opts__,
        vm,
        iso_path=iso_path,
        datastore=datastore,
        controller_key=controller_key,
        start_connected=start_connected,
        profile=profile,
    )


def attach_iso(vm, iso_path, cdrom_key=None, datastore=None, profile=None):
    """Attach an ISO to an existing CD-ROM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_cdrom.attach_iso vm-100 'isos/foo.iso' datastore=datastore-ssd-4tb
    """
    return c.attach_iso(
        __opts__, vm, iso_path, cdrom_key=cdrom_key, datastore=datastore, profile=profile
    )


def eject(vm, cdrom_key=None, profile=None):
    """Detach the ISO from an existing CD-ROM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_cdrom.eject vm-100
    """
    return c.eject(__opts__, vm, cdrom_key=cdrom_key, profile=profile)


def remove(vm, cdrom_key, profile=None):
    """Remove a CD-ROM device by key.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_cdrom.remove vm-100 3000
    """
    return c.remove(__opts__, vm, cdrom_key, profile=profile)
