"""Execution module for ESXi vMotion interface management (SOAP)."""

from saltext.vcf.clients import vim_host_vmotion as c

__virtualname__ = "vcf_vim_host_vmotion"


def __virtual__():
    return __virtualname__


def get_enabled(host, profile=None):
    """Return ``{enabled, device}`` for the host's vMotion VMkernel NIC.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_vmotion.get_enabled esxi-01
    """
    return c.get_enabled(__opts__, host, profile=profile)


def enable(host, device="vmk0", profile=None):
    """Select *device* as the vMotion VMkernel NIC.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_vmotion.enable esxi-01 device=vmk1
    """
    return c.enable(__opts__, host, device, profile=profile)


def disable(host, profile=None):
    """Deselect the host's vMotion VMkernel NIC.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_vmotion.disable esxi-01
    """
    return c.disable(__opts__, host, profile=profile)
