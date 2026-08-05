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


def find_by_name(name, profile=None):
    """Find by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_folder.find_by_name <name>

    """
    return c.find_by_name(__opts__, name, profile=profile)


def create(name, folder_type, parent=None, datacenter=None, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_folder.create <name> <folder_type>

    """
    return c.create(__opts__, name, folder_type, parent=parent, datacenter=datacenter, profile=profile)


def delete(folder_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_folder.delete <folder_id>

    """
    return c.delete(__opts__, folder_id, profile=profile)
