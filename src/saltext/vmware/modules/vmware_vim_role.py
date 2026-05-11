"""Execution module for vCenter authorization roles (SOAP)."""

from saltext.vmware.clients import vim_role as c

__virtualname__ = "vmware_vim_role"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all roles.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.list_
    """
    return c.list_(__opts__, profile=profile)


def get(name, profile=None):
    """Get a single role by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.get <name>
    """
    return c.get(__opts__, name, profile=profile)


def get_or_none(name, profile=None):
    """Return the role or ``None`` if missing.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.get_or_none <name>
    """
    return c.get_or_none(__opts__, name, profile=profile)


def create(name, privileges, profile=None):
    """Create a custom role with the given privilege ids.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.create MyRole '["System.View","System.Read"]'
    """
    return c.create(__opts__, name, privileges, profile=profile)


def update(name, privileges, profile=None):
    """Replace the privilege set on an existing role.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.update MyRole '["System.View"]'
    """
    return c.update(__opts__, name, privileges, profile=profile)


def rename(name, new_name, profile=None):
    """Rename a role.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.rename OldName NewName
    """
    return c.rename(__opts__, name, new_name, profile=profile)


def delete(name, fail_if_used=True, profile=None):
    """Delete a role.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.delete MyRole
    """
    return c.delete(__opts__, name, fail_if_used=fail_if_used, profile=profile)


def list_privileges(profile=None):
    """Return the catalog of all privileges known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_role.list_privileges
    """
    return c.list_privileges(__opts__, profile=profile)
