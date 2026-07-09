"""Execution module for VCF Operations alert and symptom definitions."""

from saltext.vcf.clients import vcfops_alert as c

__virtualname__ = "vcf_vcfops_alert"


def __virtual__():
    return __virtualname__


def alerts_list(page=0, page_size=1000):
    """Alerts list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.alerts_list <page> <page_size>

    """
    return c.alerts_list(__opts__, page=page, page_size=page_size)


def alerts_get(alert_id):
    """Alerts get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.alerts_get <alert_id>

    """
    return c.alerts_get(__opts__, alert_id)


def alerts_create(spec, profile=None):
    """Create an alert definition.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.alerts_create '{"name": "...", ...}'

    """
    return c.alerts_create(__opts__, spec, profile=profile)


def alerts_update(alert_id, spec, profile=None):
    """Update the alert definition identified by ``alert_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.alerts_update <alert_id> '{"name": "...", ...}'

    """
    return c.alerts_update(__opts__, alert_id, spec, profile=profile)


def alerts_delete(alert_id, profile=None):
    """Delete the alert definition identified by ``alert_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.alerts_delete <alert_id>

    """
    return c.alerts_delete(__opts__, alert_id, profile=profile)


def symptoms_list(page=0, page_size=1000):
    """Symptoms list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.symptoms_list <page> <page_size>

    """
    return c.symptoms_list(__opts__, page=page, page_size=page_size)


def symptoms_get(symptom_id):
    """Symptoms get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.symptoms_get <symptom_id>

    """
    return c.symptoms_get(__opts__, symptom_id)


def symptoms_create(spec, profile=None):
    """Create a symptom definition.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.symptoms_create '{"name": "...", ...}'

    """
    return c.symptoms_create(__opts__, spec, profile=profile)


def symptoms_update(symptom_id, spec, profile=None):
    """Update the symptom definition identified by ``symptom_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.symptoms_update <symptom_id> '{"name": "...", ...}'

    """
    return c.symptoms_update(__opts__, symptom_id, spec, profile=profile)


def symptoms_delete(symptom_id, profile=None):
    """Delete the symptom definition identified by ``symptom_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.symptoms_delete <symptom_id>

    """
    return c.symptoms_delete(__opts__, symptom_id, profile=profile)


def active_list(page=0, page_size=1000, **params):
    """List active alerts. Extra kwargs become server-side filters.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.active_list <page> <page_size>

    """
    return c.active_list(__opts__, page=page, page_size=page_size, params=params or None)


def active_get(alert_id):
    """Active get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_alert.active_get <alert_id>

    """
    return c.active_get(__opts__, alert_id)
