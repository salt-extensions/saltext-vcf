"""Execution module for SDDC Manager CEIP participation.

On VCF the Customer Experience Improvement Program is controlled at the
SDDC Manager level -- the older per-vCenter ``/api/appliance/ceip`` REST
endpoint does not exist on VCF 9.x builds. See
:mod:`saltext.vcf.clients.sddc_ceip` for the full endpoint contract.
"""

from saltext.vcf.clients import sddc_ceip as c
from saltext.vcf.clients import sddc_tasks

__virtualname__ = "vcf_sddc_ceip"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Return the raw CEIP body ``{"status": ..., "instanceId": ...}``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.get

    """
    return c.get(__opts__, profile=profile)


def status(profile=None):
    """Return just the current CEIP status string.

    One of ``ENABLED``, ``DISABLED``, ``ENABLING``, ``DISABLING``,
    ``ENABLING_FAILED``, ``DISABLING_FAILED``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.status

    """
    return c.status(__opts__, profile=profile)


def is_enabled(profile=None):
    """True iff CEIP is fully ``ENABLED``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.is_enabled

    """
    return c.is_enabled(__opts__, profile=profile)


def set_(enabled, profile=None):
    """PATCH the CEIP status; returns the async task body.

    *enabled* is a boolean. PATCH is asynchronous; pair with
    :func:`wait` (or :mod:`vcf_sddc_tasks`) to block until settled.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.set_ enabled=False

    """
    return c.set_(__opts__, enabled, profile=profile)


def enable(profile=None):
    """Opt in to CEIP. Async; returns the task body.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.enable

    """
    return c.enable(__opts__, profile=profile)


def disable(profile=None):
    """Opt out of CEIP (912-controls / STIG). Async; returns the task body.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.disable

    """
    return c.disable(__opts__, profile=profile)


def wait(task_id, timeout=3600, poll_interval=10, profile=None):
    """Block until the CEIP task (or any SDDC task) reaches a terminal status.

    Convenience passthrough to :func:`sddc_tasks.wait`.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_sddc_ceip.wait <task-id>

    """
    return sddc_tasks.wait(
        __opts__, task_id, timeout=timeout, poll_interval=poll_interval, profile=profile
    )
