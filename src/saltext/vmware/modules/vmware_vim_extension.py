"""Execution module for vCenter extension/plugin registration (SOAP)."""

from saltext.vmware.clients import vim_extension as c

__virtualname__ = "vmware_vim_extension"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_extension.list_

    """
    return c.list_(__opts__, profile=profile)


def get(key, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_extension.get <key>

    """
    return c.get(__opts__, key, profile=profile)


def get_or_none(key, profile=None):
    """Get or none.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_extension.get_or_none <key>

    """
    return c.get_or_none(__opts__, key, profile=profile)


def register(key, version, description, company, profile=None, **fields):
    """Register.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_extension.register <key> <version> <description> <company>

    """
    return c.register(__opts__, key, version, description, company, profile=profile, **fields)


def update(key, version=None, description=None, profile=None, **fields):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_extension.update <key> <version> <description>

    """
    return c.update(
        __opts__, key, version=version, description=description, profile=profile, **fields
    )


def unregister(key, profile=None):
    """Unregister.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_extension.unregister <key>

    """
    return c.unregister(__opts__, key, profile=profile)
