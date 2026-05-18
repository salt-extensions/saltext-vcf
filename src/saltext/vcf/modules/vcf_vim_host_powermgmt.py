"""Execution module for ESXi power-management policy (SOAP)."""

from saltext.vcf.clients import vim_host_powermgmt as c

__virtualname__ = "vcf_vim_host_powermgmt"


def __virtual__():
    return __virtualname__


def list_policies(host, profile=None):
    """List available power policies on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_powermgmt.list_policies <host>

    """
    return c.list_policies(__opts__, host, profile=profile)


def get_policy(host, profile=None):
    """Return the currently active power policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_powermgmt.get_policy <host>

    """
    return c.get_policy(__opts__, host, profile=profile)


def set_policy(host, policy_key, profile=None):
    """Set the active power policy by integer key.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_powermgmt.set_policy <host> <policy_key>

    """
    return c.set_policy(__opts__, host, policy_key, profile=profile)
