"""Execution module for VCF Installer system inventory."""

from saltext.vcf.clients import installer_system as c

__virtualname__ = "vcf_installer_system"


def __virtual__():
    return __virtualname__


def status(profile=None):
    """Return installer health + readiness.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.status
    """
    return c.status(__opts__, profile=profile)


def version(profile=None):
    """Return installer version metadata.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.version
    """
    return c.version(__opts__, profile=profile)


def registration(profile=None):
    """Return Customer Connect / VCF registration state.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.registration
    """
    return c.registration(__opts__, profile=profile)


def dns_config(profile=None):
    """Return the installer appliance's own DNS configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.dns_config
    """
    return c.dns_config(__opts__, profile=profile)


def update_dns_config(dns_servers, search_domains=None, profile=None):
    """Update the installer appliance's DNS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.update_dns_config '[10.0.0.1]'
    """
    return c.update_dns_config(
        __opts__, dns_servers, search_domains=search_domains, profile=profile
    )


def ntp_config(profile=None):
    """Return the installer appliance's NTP config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.ntp_config
    """
    return c.ntp_config(__opts__, profile=profile)


def update_ntp_config(ntp_servers, profile=None):
    """Update the installer appliance's NTP config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.update_ntp_config '[time.example.com]'
    """
    return c.update_ntp_config(__opts__, ntp_servers, profile=profile)


def identity_broker(profile=None):
    """Return Identity Broker config the installer will hand off.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.identity_broker
    """
    return c.identity_broker(__opts__, profile=profile)


def sddc_manager(profile=None):
    """Return SDDC Manager info post-bringup.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_system.sddc_manager
    """
    return c.sddc_manager(__opts__, profile=profile)
