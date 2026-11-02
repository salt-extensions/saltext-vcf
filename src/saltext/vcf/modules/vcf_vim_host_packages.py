"""Execution module for ESXi installed software packages (VIBs, SOAP)."""

from saltext.vcf.clients import vim_host_packages as c

__virtualname__ = "vcf_vim_host_packages"


def __virtual__():
    return __virtualname__


def list_(host, pkg_name=None, profile=None):
    """List the VIB packages installed on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_packages.list_ esxi-01
    """
    return c.list_(__opts__, host, pkg_name, profile=profile)
