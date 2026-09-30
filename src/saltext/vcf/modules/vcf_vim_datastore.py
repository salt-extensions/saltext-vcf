"""Execution module for vCenter-level datastore lifecycle (SOAP)."""

from saltext.vcf.clients import vim_datastore as c

__virtualname__ = "vcf_vim_datastore"


def __virtual__():
    return __virtualname__


def get(datastore, profile=None):
    """Return the full datastore dict (summary + VMFS uuid/extents + folder path).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore.get ds1
    """
    return c.get(__opts__, datastore, profile=profile)


def list_(
    datacenter=None,
    cluster=None,
    host=None,
    datastore_names=None,
    backing_disk_ids=None,
    backing_disk_scsi_addresses=None,
    profile=None,
):
    """List datastores with VMFS detail and optional filters.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore.list_ datastore_names='[ds1, ds2]'
    """
    return c.list_(
        __opts__,
        datacenter=datacenter,
        cluster=cluster,
        host=host,
        datastore_names=datastore_names,
        backing_disk_ids=backing_disk_ids,
        backing_disk_scsi_addresses=backing_disk_scsi_addresses,
        profile=profile,
    )


def maintenance_mode(datastore, profile=None):
    """Put a datastore in maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore.maintenance_mode ds1
    """
    return c.enter_maintenance(__opts__, datastore, profile=profile)


def exit_maintenance_mode(datastore, profile=None):
    """Take a datastore out of maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore.exit_maintenance_mode ds1
    """
    return c.exit_maintenance(__opts__, datastore, profile=profile)


def list_disk_partitions(host, disk_id=None, scsi_address=None, profile=None):
    """List the partition table of a disk on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_datastore.list_disk_partitions esxi-01 disk_id=naa.0001
    """
    return c.disk_partitions(__opts__, host, disk_id=disk_id, scsi_address=scsi_address, profile=profile)
