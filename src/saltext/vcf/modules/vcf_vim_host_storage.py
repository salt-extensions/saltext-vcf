"""Execution module for ESXi HBA/VMFS rescan."""

from saltext.vcf.clients import vim_host_storage as c

__virtualname__ = "vcf_vim_host_storage"


def __virtual__():
    return __virtualname__


def rescan_all_hba(host, profile=None):
    """Rescan all HBAs on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.rescan_all_hba <host>
    """
    return c.rescan_all_hba(__opts__, host, profile=profile)


def rescan_vmfs(host, profile=None):
    """Rescan for new VMFS volumes on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.rescan_vmfs <host>
    """
    return c.rescan_vmfs(__opts__, host, profile=profile)


def refresh(host, profile=None):
    """Refresh the storage system state for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.refresh <host>
    """
    return c.refresh(__opts__, host, profile=profile)


def scsi_luns(
    host,
    lun_name=None,
    state=None,
    disk_ids=None,
    scsi_addresses=None,
    ssd=None,
    profile=None,
):
    """List SCSI LUNs on *host* with full detail and optional filters.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.scsi_luns esxi-01 ssd=true
    """
    return c.scsi_luns(
        __opts__,
        host,
        lun_name=lun_name,
        state=state,
        disk_ids=disk_ids,
        scsi_addresses=scsi_addresses,
        ssd=ssd,
        profile=profile,
    )


def list_ssds(host, profile=None):
    """List SSD-classified SCSI disks on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.list_ssds esxi-01
    """
    return c.scsi_luns(__opts__, host, ssd=True, profile=profile)


def list_non_ssds(host, profile=None):
    """List non-SSD SCSI disks on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.list_non_ssds esxi-01
    """
    return c.scsi_luns(__opts__, host, ssd=False, profile=profile)


def attach_lun(host, lun_canonical_name, profile=None):
    """Attach a SCSI LUN to *host* (idempotent).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.attach_lun esxi-01 naa.000000000000001
    """
    return c.attach_lun(__opts__, host, lun_canonical_name, profile=profile)


def detach_lun(host, lun_canonical_name, profile=None):
    """Detach a SCSI LUN from *host* (idempotent).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_storage.detach_lun esxi-01 naa.000000000000001
    """
    return c.detach_lun(__opts__, host, lun_canonical_name, profile=profile)
