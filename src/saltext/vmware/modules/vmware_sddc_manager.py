"""Execution module for SDDC Manager appliance info (/v1/sddc-manager)."""

from saltext.vmware.clients import sddc_manager as c

__virtualname__ = "vmware_sddc_manager"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_sddc_manager.get

    """
    return c.get(__opts__, profile=profile)
