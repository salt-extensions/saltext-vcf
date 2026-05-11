"""Execution module for vCenter-managed ESXi host config (SOAP)."""

from saltext.vmware.clients import vim_host_config as c

__virtualname__ = "vmware_vim_host_config"


def __virtual__():
    return __virtualname__


# NTP


def ntp_get(host, profile=None):
    """Return NTP servers + ntpd service state for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ntp_get esxi-01.example.com
    """
    return c.ntp_get(__opts__, host, profile=profile)


def ntp_set_servers(host, servers, profile=None):
    """Replace the NTP server list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ntp_set_servers esxi-01.example.com '["time.example.com"]'
    """
    return c.ntp_set_servers(__opts__, host, servers, profile=profile)


def ntp_set_running(host, running, profile=None):
    """Start or stop the ntpd service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ntp_set_running esxi-01.example.com true
    """
    return c.ntp_set_running(__opts__, host, running, profile=profile)


def ntp_set_policy(host, policy, profile=None):
    """Set the ntpd start policy (``on`` | ``off`` | ``automatic``).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ntp_set_policy esxi-01.example.com on
    """
    return c.ntp_set_policy(__opts__, host, policy, profile=profile)


# Services


def service_list(host, profile=None):
    """List all services on the host.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.service_list esxi-01.example.com
    """
    return c.service_list(__opts__, host, profile=profile)


def service_start(host, service_id, profile=None):
    """Start a service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.service_start esxi-01.example.com TSM-SSH
    """
    return c.service_start(__opts__, host, service_id, profile=profile)


def service_stop(host, service_id, profile=None):
    """Stop a service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.service_stop esxi-01.example.com TSM-SSH
    """
    return c.service_stop(__opts__, host, service_id, profile=profile)


def service_restart(host, service_id, profile=None):
    """Restart a service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.service_restart esxi-01.example.com ntpd
    """
    return c.service_restart(__opts__, host, service_id, profile=profile)


def service_set_policy(host, service_id, policy, profile=None):
    """Set the start policy on a service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.service_set_policy esxi-01.example.com TSM-SSH off
    """
    return c.service_set_policy(__opts__, host, service_id, policy, profile=profile)


# Active Directory


def ad_status(host, profile=None):
    """Return AD join state for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ad_status esxi-01.example.com
    """
    return c.ad_status(__opts__, host, profile=profile)


def ad_join(host, domain, username, password, ou_path=None, profile=None):
    """Join the host to an AD domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ad_join esxi-01 example.com administrator '<pass>'
    """
    return c.ad_join(__opts__, host, domain, username, password, ou_path=ou_path, profile=profile)


def ad_leave(host, force=False, profile=None):
    """Leave the AD domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.ad_leave esxi-01 force=true
    """
    return c.ad_leave(__opts__, host, force=force, profile=profile)


# Advanced settings


def advanced_get(host, key=None, profile=None):
    """Return advanced settings (single value or full dict).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.advanced_get esxi-01 UserVars.SuppressShellWarning
    """
    return c.advanced_get(__opts__, host, key=key, profile=profile)


def advanced_set(host, key, value, profile=None):
    """Set a single advanced setting.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_config.advanced_set esxi-01 UserVars.SuppressShellWarning 1
    """
    return c.advanced_set(__opts__, host, key, value, profile=profile)
