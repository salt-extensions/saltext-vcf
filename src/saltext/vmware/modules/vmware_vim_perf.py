"""Execution module for vCenter performance counter queries (SOAP)."""

from saltext.vmware.clients import vim_perf as c

__virtualname__ = "vmware_vim_perf"


def __virtual__():
    return __virtualname__


def counters(profile=None):
    """Return the full set of vCenter perf counter definitions.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_perf.counters

    """
    return c.counters(__opts__, profile=profile)


def available_metrics(entity_mo_id, entity_type=None, profile=None):
    """Available metrics.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_perf.available_metrics <entity_mo_id> <entity_type>

    """
    return c.available_metrics(__opts__, entity_mo_id, entity_type=entity_type, profile=profile)


def query(entity_mo_id, counter_ids, **kwargs):
    """Query.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_perf.query <entity_mo_id> <counter_ids>

    """
    profile = kwargs.pop("profile", None)
    return c.query(__opts__, entity_mo_id, counter_ids, profile=profile, **kwargs)


def last_n_seconds(entity_mo_id, counter_ids, seconds=300, **kwargs):
    """Last n seconds.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_perf.last_n_seconds <entity_mo_id> <counter_ids> <seconds>

    """
    profile = kwargs.pop("profile", None)
    return c.last_n_seconds(
        __opts__, entity_mo_id, counter_ids, seconds=seconds, profile=profile, **kwargs
    )
