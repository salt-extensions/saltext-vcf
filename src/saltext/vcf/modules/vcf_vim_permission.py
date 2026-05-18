"""Execution module for vCenter object permissions (SOAP)."""

from saltext.vcf.clients import vim_permission as c

__virtualname__ = "vcf_vim_permission"


def __virtual__():
    return __virtualname__


def list_(entity_ref, inherited=True, profile=None):
    """List permissions attached to *entity_ref*.

    *entity_ref* is a bare MoID (``"vm-100"``) or ``"<type>:<moid>"``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_permission.list_ vm-100
        salt '*' vcf_vim_permission.list_ VirtualMachine:vm-100 inherited=false
    """
    return c.list_(__opts__, entity_ref, inherited=inherited, profile=profile)


def set_(entity_ref, principal, role, propagate=True, group=False, profile=None):
    """Set a permission ``(principal, role, propagate)`` on *entity_ref*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_permission.set_ vm-100 alice@vsphere.local Admin
    """
    return c.set_(
        __opts__,
        entity_ref,
        principal,
        role,
        propagate=propagate,
        group=group,
        profile=profile,
    )


def remove(entity_ref, principal, group=False, profile=None):
    """Remove the *(principal, group)* permission from *entity_ref*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_permission.remove vm-100 alice@vsphere.local
    """
    return c.remove(__opts__, entity_ref, principal, group=group, profile=profile)


def reset(entity_ref, profile=None):
    """Drop every non-inherited permission on *entity_ref*. Destructive.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_permission.reset vm-100
    """
    return c.reset(__opts__, entity_ref, profile=profile)
