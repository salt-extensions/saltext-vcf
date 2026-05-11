"""Execution module for VCF Operations alert and symptom definitions."""

from saltext.vmware.clients import vcfops_alert as c

__virtualname__ = "vmware_vcfops_alert"


def __virtual__():
    return __virtualname__


def alerts_list(page=0, page_size=1000):
    """Alerts list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_alert.alerts_list <page> <page_size>

    """
    return c.alerts_list(__opts__, page=page, page_size=page_size)


def alerts_get(alert_id):
    """Alerts get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_alert.alerts_get <alert_id>

    """
    return c.alerts_get(__opts__, alert_id)


def symptoms_list(page=0, page_size=1000):
    """Symptoms list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_alert.symptoms_list <page> <page_size>

    """
    return c.symptoms_list(__opts__, page=page, page_size=page_size)


def symptoms_get(symptom_id):
    """Symptoms get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_alert.symptoms_get <symptom_id>

    """
    return c.symptoms_get(__opts__, symptom_id)


def active_list(page=0, page_size=1000, **params):
    """List active alerts. Extra kwargs become server-side filters.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_alert.active_list <page> <page_size>

    """
    return c.active_list(__opts__, page=page, page_size=page_size, params=params or None)


def active_get(alert_id):
    """Active get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_alert.active_get <alert_id>

    """
    return c.active_get(__opts__, alert_id)
