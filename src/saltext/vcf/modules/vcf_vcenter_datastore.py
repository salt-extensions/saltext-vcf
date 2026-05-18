"""Execution module for vCenter datastores."""

from saltext.vcf.clients import vcenter_datastore as c

__virtualname__ = "vcf_vcenter_datastore"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datastore.list_

    """
    return c.list_(__opts__, profile=profile)


def get(datastore, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datastore.get <datastore>

    """
    return c.get(__opts__, datastore, profile=profile)
