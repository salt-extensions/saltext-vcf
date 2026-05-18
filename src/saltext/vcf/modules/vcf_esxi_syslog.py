"""Execution module for ESXi syslog configuration."""

from saltext.vcf.clients import esxi_syslog as c

__virtualname__ = "vcf_esxi_syslog"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_syslog.get

    """
    return c.get(__opts__, profile=profile)


def set_servers(servers, profile=None):
    """Set servers.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_syslog.set_servers <servers>

    """
    return c.set_servers(__opts__, servers, profile=profile)


def set_log_level(level, profile=None):
    """Set log level.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_esxi_syslog.set_log_level <level>

    """
    return c.set_log_level(__opts__, level, profile=profile)
