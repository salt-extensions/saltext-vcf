"""Execution module for ESXi hyperthreading toggle."""

from saltext.vcf.clients import vim_host_hyperthreading as c

__virtualname__ = "vcf_vim_host_hyperthreading"


def __virtual__():
    return __virtualname__


def get(host, profile=None):
    """Return hyperthreading state ``{available, active, config}``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_hyperthreading.get <host>
    """
    return c.get(__opts__, host, profile=profile)


def enable(host, profile=None):
    """Mark hyperthreading enabled (reboot required).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_hyperthreading.enable <host>
    """
    return c.enable(__opts__, host, profile=profile)


def disable(host, profile=None):
    """Mark hyperthreading disabled (reboot required).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_hyperthreading.disable <host>
    """
    return c.disable(__opts__, host, profile=profile)
