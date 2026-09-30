"""Execution module for host datastore lifecycle (VMFS / NFS)."""

from saltext.vcf.clients import vim_host_datastore as c

__virtualname__ = "vcf_vim_host_datastore"


def __virtual__():
    return __virtualname__


def list_(host, profile=None):
    """List datastores mounted on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.list_ <host>
    """
    return c.list_(__opts__, host, profile=profile)


def list_available_vmfs_disks(host, profile=None):
    """List raw disks on *host* eligible for a new VMFS datastore.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.list_available_vmfs_disks <host>
    """
    return c.list_available_vmfs_disks(__opts__, host, profile=profile)


def create_vmfs(host, name, device_path, vmfs_version=6, profile=None):
    """Create a VMFS datastore on a host's raw disk.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.create_vmfs <host> myds /vmfs/devices/disks/naa.xxx
    """
    return c.create_vmfs(
        __opts__, host, name, device_path, vmfs_version=vmfs_version, profile=profile
    )


def mount_nfs(
    host,
    name,
    remote_host,
    remote_path,
    access_mode="readWrite",
    type_="NFS",
    profile=None,
):
    """Mount an NFS share as a datastore on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.mount_nfs <host> nfs-iso 10.0.0.5 /export/iso
    """
    return c.mount_nfs(
        __opts__,
        host,
        name,
        remote_host,
        remote_path,
        access_mode=access_mode,
        type_=type_,
        profile=profile,
    )


def remove(host, datastore, profile=None):
    """Unmount a datastore from a host.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.remove <host> <datastore>
    """
    return c.remove(__opts__, host, datastore, profile=profile)


def rescan_storage(host, profile=None):
    """Trigger a storage HBA rescan on a host.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.rescan_storage <host>
    """
    return c.rescan_storage(__opts__, host, profile=profile)


def lun_ids(host, profile=None):
    """Return the LUN canonical names backing every datastore on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.lun_ids esxi-01
    """
    return c.lun_ids(__opts__, host, profile=profile)


def disks(host, disk_name=None, profile=None):
    """Return per-datastore VMFS backing-disk info on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.disks esxi-01 disk_name=ds1
    """
    return c.disks(__opts__, host, disk_name, profile=profile)


def mount_vmfs(host, vmfs_uuid, lun_canonical_name=None, datastore_name=None, profile=None):
    """Attach a LUN and mount an existing VMFS volume by uuid on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.mount_vmfs esxi-01 5f6b... naa.0001
    """
    return c.mount_vmfs(
        __opts__,
        host,
        vmfs_uuid,
        lun_canonical_name=lun_canonical_name,
        datastore_name=datastore_name,
        profile=profile,
    )


def unmount_vmfs(host, vmfs_uuid, detach_luns=True, profile=None):
    """Unmount a VMFS volume on *host* and optionally detach its LUNs.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_datastore.unmount_vmfs esxi-01 5f6b... detach_luns=true
    """
    return c.unmount_vmfs(
        __opts__, host, vmfs_uuid, detach_luns=detach_luns, profile=profile
    )
