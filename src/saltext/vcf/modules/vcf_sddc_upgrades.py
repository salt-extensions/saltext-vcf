"""Execution module for SDDC Manager upgrade workflows."""

from saltext.vcf.clients import sddc_upgrades as c

__virtualname__ = "vcf_sddc_upgrades"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_upgrades.list_

    """
    return c.list_(__opts__, profile=profile)


def get(upgrade_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_upgrades.get <upgrade_id>

    """
    return c.get(__opts__, upgrade_id, profile=profile)


def start(upgrade_spec, profile=None):
    """Start.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_upgrades.start <upgrade_spec>

    """
    return c.start(__opts__, upgrade_spec, profile=profile)
