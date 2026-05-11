"""Execution module for SDDC Manager software bundles."""

from saltext.vmware.clients import sddc_bundles as c

__virtualname__ = "vmware_sddc_bundles"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_bundles.list_

    """
    return c.list_(__opts__, profile=profile)


def get(bundle_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_bundles.get <bundle_id>

    """
    return c.get(__opts__, bundle_id, profile=profile)


def download(bundle_id, profile=None):
    """Download.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_bundles.download <bundle_id>

    """
    return c.download(__opts__, bundle_id, profile=profile)
