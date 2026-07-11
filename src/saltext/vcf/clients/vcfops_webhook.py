"""VCF Operations — outbound webhook instances and notification rules.

VCF Operations 9.x delivers alert/event notifications to external systems
(webhooks, ITSMs, chatops, syslog) via two related concepts:

* ``outbound-instances`` — configured *destinations* (a REST webhook,
  a syslog endpoint, etc.). Each has a ``pluginTypeId`` selecting the
  transport (``RestPlugin`` for HTTPS webhooks) and a ``configValues``
  payload with URL, headers, and other plugin-specific settings.
* ``notifications/rules`` — the *bindings* that say *"when alert X on
  resource Y fires, send it to outbound instance Z"*.

Endpoints wrapped here:

* ``GET/POST /suite-api/api/outbound-instances``
* ``GET/PUT/DELETE /suite-api/api/outbound-instances/{id}``
* ``GET/POST /suite-api/api/notifications/rules``
* ``GET/PUT/DELETE /suite-api/api/notifications/rules/{id}``
"""

import requests

from saltext.vcf.utils import vcfops

_INSTANCES = "/suite-api/api/outbound-instances"
_RULES = "/suite-api/api/notifications/rules"


# ---------------------------------------------------------------------------
# Outbound instances (webhook destinations)
# ---------------------------------------------------------------------------


def list_(opts, page=0, page_size=1000, profile=None):
    """List every configured outbound webhook / notification instance."""
    return vcfops.api_get(
        opts, _INSTANCES, params={"page": page, "pageSize": page_size}, profile=profile
    )


def get(opts, instance_id, profile=None):
    """Return the outbound instance whose id matches *instance_id*."""
    return vcfops.api_get(opts, f"{_INSTANCES}/{instance_id}", profile=profile)


def get_or_none(opts, instance_id, profile=None):
    """Like :func:`get` but returns ``None`` on a 404."""
    try:
        return get(opts, instance_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, instance_spec, profile=None):
    """Create an outbound webhook instance.

    *instance_spec* example::

        {"name": "pagerduty-prod",
         "pluginTypeId": "RestPlugin",
         "configValues": [
             {"name": "url", "value": "https://events.pagerduty.com/..."},
             {"name": "certificateThumbprint", "value": "AA:BB:..."}
         ]}
    """
    return vcfops.api_post(opts, _INSTANCES, body=instance_spec, profile=profile)


def update(opts, instance_id, instance_spec, profile=None):
    """Replace the outbound instance with id *instance_id*."""
    return vcfops.api_put(opts, f"{_INSTANCES}/{instance_id}", body=instance_spec, profile=profile)


def delete(opts, instance_id, profile=None):
    """Delete the outbound instance with id *instance_id*."""
    return vcfops.api_delete(opts, f"{_INSTANCES}/{instance_id}", profile=profile)


# ---------------------------------------------------------------------------
# Notification rules (alert -> outbound instance bindings)
# ---------------------------------------------------------------------------


def list_rules(opts, page=0, page_size=1000, profile=None):
    """List every notification rule."""
    return vcfops.api_get(
        opts, _RULES, params={"page": page, "pageSize": page_size}, profile=profile
    )


def get_rule(opts, rule_id, profile=None):
    """Return the notification rule whose id matches *rule_id*."""
    return vcfops.api_get(opts, f"{_RULES}/{rule_id}", profile=profile)


def get_rule_or_none(opts, rule_id, profile=None):
    """Like :func:`get_rule` but returns ``None`` on a 404."""
    try:
        return get_rule(opts, rule_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_rule(opts, rule_spec, profile=None):
    """Create a notification rule binding alerts to an outbound instance.

    *rule_spec* example::

        {"name": "prod-critical-to-pagerduty",
         "pluginId": "<outbound-instance-id>",
         "alertControlStates": ["OPEN"],
         "alertCriticalities": ["CRITICAL"]}
    """
    return vcfops.api_post(opts, _RULES, body=rule_spec, profile=profile)


def update_rule(opts, rule_id, rule_spec, profile=None):
    """Replace the notification rule with id *rule_id*."""
    return vcfops.api_put(opts, f"{_RULES}/{rule_id}", body=rule_spec, profile=profile)


def delete_rule(opts, rule_id, profile=None):
    """Delete the notification rule with id *rule_id*."""
    return vcfops.api_delete(opts, f"{_RULES}/{rule_id}", profile=profile)
