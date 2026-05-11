"""Execution module for vCenter KMS providers."""

from saltext.vmware.clients import vcenter_kms as c

__virtualname__ = "vmware_vcenter_kms"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_kms.list_

    """
    return c.list_(__opts__, profile=profile)


def get(provider_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_kms.get <provider_id>

    """
    return c.get(__opts__, provider_id, profile=profile)


def create(provider_spec, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_kms.create <provider_spec>

    """
    return c.create(__opts__, provider_spec, profile=profile)


def delete(provider_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_kms.delete <provider_id>

    """
    return c.delete(__opts__, provider_id, profile=profile)
