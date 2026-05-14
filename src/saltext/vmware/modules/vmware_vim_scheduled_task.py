"""Execution module for vCenter scheduled tasks."""

from saltext.vmware.clients import vim_scheduled_task as c

__virtualname__ = "vmware_vim_scheduled_task"


def __virtual__():
    return __virtualname__


def list_(entity=None, profile=None):
    """List scheduled tasks; optionally filter by entity moId.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_scheduled_task.list_

    """
    return c.list_(__opts__, entity=entity, profile=profile)


def get(task, profile=None):
    """Return one scheduled task by moId or name.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_scheduled_task.get <task>

    """
    return c.get(__opts__, task, profile=profile)


def create(entity, spec, profile=None):
    """Create a scheduled task on *entity* (moId). *spec* is a dict.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_scheduled_task.create <entity> <spec>

    """
    return c.create(__opts__, entity, spec, profile=profile)


def reconfigure(task, spec, profile=None):
    """Reconfigure an existing scheduled task.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_scheduled_task.reconfigure <task> <spec>

    """
    return c.reconfigure(__opts__, task, spec, profile=profile)


def delete(task, profile=None):
    """Remove a scheduled task.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_scheduled_task.delete <task>

    """
    return c.delete(__opts__, task, profile=profile)


def run_now(task, profile=None):
    """Trigger the action of a scheduled task immediately.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_scheduled_task.run_now <task>

    """
    return c.run_now(__opts__, task, profile=profile)
