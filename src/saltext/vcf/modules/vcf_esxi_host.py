"""Execution module for ESXi host system operations."""

from saltext.vcf.clients import esxi_host as c

__virtualname__ = "vcf_esxi_host"


def __virtual__():
    return __virtualname__


def info(profile=None):
    """Return host system info.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.info

    """
    return c.info(__opts__, profile=profile)


def lockdown_get(profile=None):
    """Lockdown get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.lockdown_get

    """
    return c.lockdown_get(__opts__, profile=profile)


def lockdown_set(mode, exception_users=None, profile=None):
    """Set lockdown mode (``NORMAL``, ``STRICT``, or ``DISABLED``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.lockdown_set <mode> <exception_users>

    """
    return c.lockdown_set(__opts__, mode, exception_users=exception_users, profile=profile)


def enter_maintenance(profile=None):
    """Enter maintenance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.enter_maintenance

    """
    return c.enter_maintenance(__opts__, profile=profile)


def exit_maintenance(profile=None):
    """Exit maintenance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.exit_maintenance

    """
    return c.exit_maintenance(__opts__, profile=profile)


def reboot(force=False, profile=None):
    """Reboot.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.reboot <force>

    """
    return c.reboot(__opts__, force=force, profile=profile)


def shutdown(force=False, profile=None):
    """Shutdown.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_host.shutdown <force>

    """
    return c.shutdown(__opts__, force=force, profile=profile)
