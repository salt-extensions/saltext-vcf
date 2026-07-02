"""VCF Operations — alert and symptom definitions, plus active alerts.

Three distinct concepts:

- ``alertdefinitions`` (catalog) — the configurable templates that say
  *if X then alert*.
- ``symptomdefinitions`` (catalog) — the conditions alerts compose from.
- ``alerts`` (instances) — open/active alerts firing right now against
  monitored resources.
"""

import requests

from saltext.vcf.utils import vcfops

_ALERTS = "/suite-api/api/alertdefinitions"
_SYMPTOMS = "/suite-api/api/symptomdefinitions"
_ACTIVE = "/suite-api/api/alerts"


def alerts_list(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _ALERTS, params={"page": page, "pageSize": page_size})


def alerts_get(opts, alert_id):
    return vcfops.api_get(opts, f"{_ALERTS}/{alert_id}")


def alerts_create(opts, spec, profile=None):
    """Create a new alert definition.

    *spec* is the ``AlertDefinition`` body VCF Operations expects — the
    same shape returned by :func:`alerts_get`. Returns the persisted
    definition (typically with a server-assigned ``id``).
    """
    return vcfops.api_post(opts, _ALERTS, body=spec, profile=profile)


def alerts_update(opts, alert_id, spec, profile=None):
    """Update the alert definition identified by *alert_id*.

    *spec* is the full ``AlertDefinition`` replacement body (the
    ``alertdefinitions`` endpoint is PUT-shaped, not PATCH). Returns the
    persisted definition.
    """
    return vcfops.api_put(opts, f"{_ALERTS}/{alert_id}", body=spec, profile=profile)


def alerts_delete(opts, alert_id, profile=None):
    """Delete the alert definition identified by *alert_id*.

    Returns ``{}`` on success.
    """
    return vcfops.api_delete(opts, f"{_ALERTS}/{alert_id}", profile=profile)


def alerts_get_or_none(opts, alert_id):
    try:
        return alerts_get(opts, alert_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def symptoms_list(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _SYMPTOMS, params={"page": page, "pageSize": page_size})


def symptoms_get(opts, symptom_id):
    return vcfops.api_get(opts, f"{_SYMPTOMS}/{symptom_id}")


def symptoms_create(opts, spec, profile=None):
    """Create a new symptom definition.

    *spec* is the ``SymptomDefinition`` body VCF Operations expects — the
    same shape returned by :func:`symptoms_get`. Returns the persisted
    definition (typically with a server-assigned ``id``).
    """
    return vcfops.api_post(opts, _SYMPTOMS, body=spec, profile=profile)


def symptoms_update(opts, symptom_id, spec, profile=None):
    """Update the symptom definition identified by *symptom_id*.

    *spec* is the full replacement body. Returns the persisted definition.
    """
    return vcfops.api_put(opts, f"{_SYMPTOMS}/{symptom_id}", body=spec, profile=profile)


def symptoms_delete(opts, symptom_id, profile=None):
    """Delete the symptom definition identified by *symptom_id*.

    Returns ``{}`` on success.
    """
    return vcfops.api_delete(opts, f"{_SYMPTOMS}/{symptom_id}", profile=profile)


def symptoms_get_or_none(opts, symptom_id):
    try:
        return symptoms_get(opts, symptom_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def active_list(opts, page=0, page_size=1000, params=None):
    """List active (open) alerts.

    Extra *params* are merged in for server-side filtering — e.g.
    ``{"activeOnly": True, "resourceId": "<uuid>"}``.
    """
    base = {"page": page, "pageSize": page_size}
    if params:
        base.update(params)
    return vcfops.api_get(opts, _ACTIVE, params=base)


def active_get(opts, alert_id):
    return vcfops.api_get(opts, f"{_ACTIVE}/{alert_id}")


def active_get_or_none(opts, alert_id):
    try:
        return active_get(opts, alert_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
