"""Execution module for SOAP host maintenance with evacuation policy."""

from saltext.vmware.clients import vim_host_maintenance as c

__virtualname__ = "vmware_vim_host_maintenance"


def __virtual__():
    return __virtualname__


def is_in(host, profile=None):
    """True if *host* is in maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_maintenance.is_in <host>

    """
    return c.is_in(__opts__, host, profile=profile)


def enter(host, evacuate_powered_off_vms=False, vsan_mode=None, timeout=0, profile=None):
    """Enter maintenance mode with optional evacuation and vSAN mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_maintenance.enter <host> evacuate_powered_off_vms=True

    """
    return c.enter(
        __opts__,
        host,
        evacuate_powered_off_vms=evacuate_powered_off_vms,
        vsan_mode=vsan_mode,
        timeout=timeout,
        profile=profile,
    )


def exit_(host, timeout=0, profile=None):
    """Exit maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_maintenance.exit_ <host>

    """
    return c.exit_(__opts__, host, timeout=timeout, profile=profile)
