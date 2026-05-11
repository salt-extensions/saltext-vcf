"""Execution module for vCenter alarm management (SOAP)."""

from saltext.vmware.clients import vim_alarm as c

__virtualname__ = "vmware_vim_alarm"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_alarm.list_

    """
    return c.list_(__opts__, profile=profile)


def get(name, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_alarm.get <name>

    """
    return c.get(__opts__, name, profile=profile)


def create(name, description, expression, action=None, enabled=True, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_alarm.create <name> <description> <expression> <action> <enabled>

    """
    return c.create(
        __opts__,
        name,
        description,
        expression,
        action=action,
        enabled=enabled,
        profile=profile,
    )


def update(alarm_mo_id, profile=None, **fields):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_alarm.update <alarm_mo_id>

    """
    return c.update(__opts__, alarm_mo_id, profile=profile, **fields)


def delete(alarm_mo_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_alarm.delete <alarm_mo_id>

    """
    return c.delete(__opts__, alarm_mo_id, profile=profile)
