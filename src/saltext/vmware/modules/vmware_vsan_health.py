"""Execution module for vSAN cluster health checks (SOAP)."""

from saltext.vmware.clients import vsan_health as c

__virtualname__ = "vmware_vsan_health"


def __virtual__():
    return __virtualname__


def summary(cluster, fetch_from_cache=True, profile=None):
    """Summary.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_health.summary <cluster> <fetch_from_cache>

    """
    return c.summary(__opts__, cluster, fetch_from_cache=fetch_from_cache, profile=profile)


def groups(cluster, fetch_from_cache=True, profile=None):
    """Groups.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_health.groups <cluster> <fetch_from_cache>

    """
    return c.groups(__opts__, cluster, fetch_from_cache=fetch_from_cache, profile=profile)


def overall(cluster, fetch_from_cache=True, profile=None):
    """Overall.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_health.overall <cluster> <fetch_from_cache>

    """
    return c.overall(__opts__, cluster, fetch_from_cache=fetch_from_cache, profile=profile)


def silenced_checks(cluster, profile=None):
    """Silenced checks.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_health.silenced_checks <cluster>

    """
    return c.silenced_checks(__opts__, cluster, profile=profile)


def silence(cluster, checks, profile=None):
    """Silence.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_health.silence <cluster> <checks>

    """
    return c.silence(__opts__, cluster, checks, profile=profile)


def unsilence(cluster, checks, profile=None):
    """Unsilence.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vsan_health.unsilence <cluster> <checks>

    """
    return c.unsilence(__opts__, cluster, checks, profile=profile)
