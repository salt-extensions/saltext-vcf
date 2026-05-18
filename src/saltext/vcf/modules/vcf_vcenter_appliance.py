"""Execution module for vCenter appliance APIs."""

from saltext.vcf.clients import vcenter_appliance as c

__virtualname__ = "vcf_vcenter_appliance"


def __virtual__():
    return __virtualname__


# Services
def services_list(profile=None):
    """Services list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.services_list

    """
    return c.services_list(__opts__, profile=profile)


def services_get(service, profile=None):
    """Services get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.services_get <service>

    """
    return c.services_get(__opts__, service, profile=profile)


def services_start(service, profile=None):
    """Services start.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.services_start <service>

    """
    return c.services_start(__opts__, service, profile=profile)


def services_stop(service, profile=None):
    """Services stop.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.services_stop <service>

    """
    return c.services_stop(__opts__, service, profile=profile)


def services_restart(service, profile=None):
    """Services restart.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.services_restart <service>

    """
    return c.services_restart(__opts__, service, profile=profile)


# System
def version(profile=None):
    """Version.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.version

    """
    return c.version(__opts__, profile=profile)


def health_system(profile=None):
    """Health system.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.health_system

    """
    return c.health_system(__opts__, profile=profile)


# DNS
def dns_get(profile=None):
    """Dns get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.dns_get

    """
    return c.dns_get(__opts__, profile=profile)


def dns_set(servers, mode="is_static", profile=None):
    """Dns set.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.dns_set <servers> <mode>

    """
    return c.dns_set(__opts__, servers, mode=mode, profile=profile)


# Syslog
def logging_forwarding_get(profile=None):
    """Logging forwarding get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.logging_forwarding_get

    """
    return c.logging_forwarding_get(__opts__, profile=profile)


def logging_forwarding_set(servers, profile=None):
    """Logging forwarding set.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_appliance.logging_forwarding_set <servers>

    """
    return c.logging_forwarding_set(__opts__, servers, profile=profile)
