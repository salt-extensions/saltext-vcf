"""Execution module for vCenter Server statistics collection intervals."""

from saltext.vcf.clients import vcenter_statistics as c

__virtualname__ = "vcf_vcenter_statistics"


def __virtual__():
    return __virtualname__


def intervals_get(profile=None):
    """Intervals get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_statistics.intervals_get

    """
    return c.intervals_get(__opts__, profile=profile)


def interval_get(name, profile=None):
    """Interval get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_statistics.interval_get past_day

    """
    return c.interval_get(__opts__, name, profile=profile)


def interval_set(name, enabled=None, interval_minutes=None, save_days=None, level=None, profile=None):
    """Interval set.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_statistics.interval_set past_day level=2

    """
    return c.interval_set(
        __opts__,
        name,
        enabled=enabled,
        interval_minutes=interval_minutes,
        save_days=save_days,
        level=level,
        profile=profile,
    )
