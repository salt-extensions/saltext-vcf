"""Execution module for vSphere licenses."""

from saltext.vmware.clients import vim_license as c

__virtualname__ = "vmware_vim_license"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List every license known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.list_
    """
    return c.list_(__opts__, profile=profile)


def get(license_key, profile=None):
    """Return one license by key.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.get <license_key>
    """
    return c.get(__opts__, license_key, profile=profile)


def add(license_key, labels=None, profile=None):
    """Register a license.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.add <license_key>
    """
    return c.add(__opts__, license_key, labels=labels, profile=profile)


def remove(license_key, profile=None):
    """Remove a license.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.remove <license_key>
    """
    return c.remove(__opts__, license_key, profile=profile)


def assigned_list(entity_id=None, profile=None):
    """List license assignments.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.assigned_list
    """
    return c.assigned_list(__opts__, entity_id=entity_id, profile=profile)


def assign(entity_id, license_key, name=None, profile=None):
    """Assign a license to an entity.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.assign <entity_id> <license_key>
    """
    return c.assign(__opts__, entity_id, license_key, name=name, profile=profile)


def unassign(entity_id, profile=None):
    """Remove the license assignment from an entity.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_license.unassign <entity_id>
    """
    return c.unassign(__opts__, entity_id, profile=profile)
