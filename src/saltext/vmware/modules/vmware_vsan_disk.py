"""Execution module for vSAN disk and disk-group management (SOAP)."""

from saltext.vmware.clients import vsan_disk as c

__virtualname__ = "vmware_vsan_disk"


def __virtual__():
    return __virtualname__


def host_status(host, profile=None):
    """Host status.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_disk.host_status <host>

    """
    return c.host_status(__opts__, host, profile=profile)


def host_config(host, profile=None):
    """Host config.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_disk.host_config <host>

    """
    return c.host_config(__opts__, host, profile=profile)


def host_disk_mapping(host, profile=None):
    """Host disk mapping.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_disk.host_disk_mapping <host>

    """
    return c.host_disk_mapping(__opts__, host, profile=profile)


def query_disks_for_filter(host, profile=None):
    """Query disks for filter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_disk.query_disks_for_filter <host>

    """
    return c.query_disks_for_filter(__opts__, host, profile=profile)


def add_disks(host, disks, profile=None):
    """Add disks.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_disk.add_disks <host> <disks>

    """
    return c.add_disks(__opts__, host, disks, profile=profile)


def remove_disks(host, disks, maintenance_mode_action="ensureObjectAccessibility", profile=None):
    """Remove disks.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_disk.remove_disks <host> <disks> <maintenance_mode_action>

    """
    return c.remove_disks(
        __opts__,
        host,
        disks,
        maintenance_mode_action=maintenance_mode_action,
        profile=profile,
    )
