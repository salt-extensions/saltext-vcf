"""Execution module for ESXi kernel-module config (SOAP)."""

from saltext.vmware.clients import vim_host_kernel_module as c

__virtualname__ = "vmware_vim_host_kernel_module"


def __virtual__():
    return __virtualname__


def list_(host, profile=None):
    """List kernel modules on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_kernel_module.list_ <host>

    """
    return c.list_(__opts__, host, profile=profile)


def get_options(host, module, profile=None):
    """Return the configured option string for *module*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_kernel_module.get_options <host> <module>

    """
    return c.get_options(__opts__, host, module, profile=profile)


def set_options(host, module, options, profile=None):
    """Set the kernel-module option string.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_kernel_module.set_options <host> <module> <options>

    """
    return c.set_options(__opts__, host, module, options, profile=profile)
