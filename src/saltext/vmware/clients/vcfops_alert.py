"""VCF Operations — alert and symptom definitions, plus active alerts.

Three distinct concepts:

- ``alertdefinitions`` (catalog) — the configurable templates that say
  *if X then alert*.
- ``symptomdefinitions`` (catalog) — the conditions alerts compose from.
- ``alerts`` (instances) — open/active alerts firing right now against
  monitored resources.
"""

import requests

from saltext.vmware.utils import vcfops

_ALERTS = "/suite-api/api/alertdefinitions"
_SYMPTOMS = "/suite-api/api/symptomdefinitions"
_ACTIVE = "/suite-api/api/alerts"


def alerts_list(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _ALERTS, params={"page": page, "pageSize": page_size})


def alerts_get(opts, alert_id):
    return vcfops.api_get(opts, f"{_ALERTS}/{alert_id}")


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
