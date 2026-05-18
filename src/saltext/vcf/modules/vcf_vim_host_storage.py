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
