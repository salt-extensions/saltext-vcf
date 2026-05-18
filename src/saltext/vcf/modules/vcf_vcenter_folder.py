"""Execution module for vCenter folders."""

from saltext.vcf.clients import vcenter_folder as c

__virtualname__ = "vcf_vcenter_folder"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_folder.list_

    """
    return c.list_(__opts__, profile=profile)


def get(folder_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_folder.get <folder_id>

    """
    return c.get(__opts__, folder_id, profile=profile)


def list_by_type(folder_type, profile=None):
    """List by type.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_folder.list_by_type <folder_type>

    """
    return c.list_by_type(__opts__, folder_type, profile=profile)
