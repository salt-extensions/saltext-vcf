"""Execution module for ESXi ``/etc/rc.local.d/local.sh`` custom boot commands."""

from saltext.vcf.clients import esxi_localsh as c

__virtualname__ = "vcf_esxi_localsh"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_localsh.get

    """
    return c.get(__opts__, profile=profile)


def apply(content, execute=True, profile=None):
    """Apply.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_localsh.apply "#!/bin/sh\\nexit 0"

    """
    return c.apply(__opts__, content, execute=execute, profile=profile)
