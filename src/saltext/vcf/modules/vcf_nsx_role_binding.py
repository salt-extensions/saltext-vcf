"""Execution module for NSX RBAC role bindings."""

from saltext.vcf.clients import nsx_role_binding as c

__virtualname__ = "vcf_nsx_role_binding"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_role_binding.list_

    """
    return c.list_(__opts__, profile=profile)


def get(binding_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_role_binding.get <binding_id>

    """
    return c.get(__opts__, binding_id, profile=profile)


def create(name, type_, roles, profile=None, **spec):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_role_binding.create <name> <type_> <roles>

    """
    return c.create(__opts__, name, type_, roles, profile=profile, **spec)


def update(binding_id, body, profile=None):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_role_binding.update <binding_id> <body>

    """
    return c.update(__opts__, binding_id, body, profile=profile)


def delete(binding_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_role_binding.delete <binding_id>

    """
    return c.delete(__opts__, binding_id, profile=profile)
