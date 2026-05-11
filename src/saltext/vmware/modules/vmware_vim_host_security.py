"""Execution module for host lockdown, local users, and iSCSI."""

from saltext.vmware.clients import vim_host_security as c

__virtualname__ = "vmware_vim_host_security"


def __virtual__():
    return __virtualname__


# Lockdown


def lockdown_get(host, profile=None):
    """Return the host's lockdown mode + exception user list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.lockdown_get esxi-01
    """
    return c.lockdown_get(__opts__, host, profile=profile)


def lockdown_set(host, mode, profile=None):
    """Set lockdown *mode* (``lockdownDisabled`` | ``lockdownNormal`` | ``lockdownStrict``).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.lockdown_set esxi-01 lockdownNormal
    """
    return c.lockdown_set(__opts__, host, mode, profile=profile)


def lockdown_set_exception_users(host, users, profile=None):
    """Replace the lockdown-mode exception-user list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.lockdown_set_exception_users esxi-01 '["root","ops"]'
    """
    return c.lockdown_set_exception_users(__opts__, host, users, profile=profile)


# Local users


def user_list(host, search_str="", exact=False, profile=None):
    """List local users matching *search_str* (empty = all).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.user_list esxi-01
    """
    return c.user_list(__opts__, host, search_str=search_str, exact=exact, profile=profile)


def user_create(host, username, password, description="", profile=None):
    """Create a local user on the host.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.user_create esxi-01 ops '<pw>'
    """
    return c.user_create(
        __opts__, host, username, password, description=description, profile=profile
    )


def user_update(host, username, password=None, description=None, profile=None):
    """Update an existing local user.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.user_update esxi-01 ops description="ops user"
    """
    return c.user_update(
        __opts__, host, username, password=password, description=description, profile=profile
    )


def user_delete(host, username, profile=None):
    """Delete a local user.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.user_delete esxi-01 ops
    """
    return c.user_delete(__opts__, host, username, profile=profile)


# iSCSI


def iscsi_status(host, profile=None):
    """Return software iSCSI initiator status + targets.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.iscsi_status esxi-01
    """
    return c.iscsi_status(__opts__, host, profile=profile)


def iscsi_enable(host, profile=None):
    """Enable software iSCSI on the host and return the HBA device.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.iscsi_enable esxi-01
    """
    return c.iscsi_enable(__opts__, host, profile=profile)


def iscsi_disable(host, profile=None):
    """Disable software iSCSI on the host.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.iscsi_disable esxi-01
    """
    return c.iscsi_disable(__opts__, host, profile=profile)


def iscsi_add_send_target(host, address, port=3260, profile=None):
    """Add a Send Targets discovery address.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.iscsi_add_send_target esxi-01 10.0.0.50
    """
    return c.iscsi_add_send_target(__opts__, host, address, port=port, profile=profile)


def iscsi_remove_send_target(host, address, port=3260, profile=None):
    """Remove a Send Targets discovery address.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.iscsi_remove_send_target esxi-01 10.0.0.50
    """
    return c.iscsi_remove_send_target(__opts__, host, address, port=port, profile=profile)


def iscsi_set_chap(host, name, password, direction="prohibited", profile=None):
    """Configure CHAP on the software iSCSI initiator.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_security.iscsi_set_chap esxi-01 chap-user '<pw>' direction=required
    """
    return c.iscsi_set_chap(
        __opts__, host, name=name, password=password, direction=direction, profile=profile
    )
