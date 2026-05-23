"""VCF Automation — event-broker action subscriptions (``/event-broker/api/subscriptions``).

A subscription fires an ABX action (or vRO workflow) when an event
topic publishes. Common topics: ``compute.provision.post``,
``deployment.action.pre``, ``deployment.action.post``.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/event-broker/api/subscriptions"
_TOPICS = "/event-broker/api/event-topics"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("content", []) or []


def get(opts, subscription_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{subscription_id}", profile=profile)


def get_or_none(opts, subscription_id, profile=None):
    try:
        return get(opts, subscription_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create an event subscription.

    *spec* keys: ``name``, ``description``, ``eventTopicId``,
    ``runnableType`` (``extensibility.abx`` / ``extensibility.vro``),
    ``runnableId``, ``criteria`` (vRO-style filter expression),
    ``recoverRunnableType``, ``recoverRunnableId``, ``constraints``,
    ``disabled``, ``priority``, ``timeout``, ``blocking``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, subscription_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{subscription_id}", body=spec, profile=profile)


def delete(opts, subscription_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{subscription_id}", profile=profile)


def list_event_topics(opts, profile=None):
    """Return every event topic the broker exposes (the catalog of
    ``eventTopicId`` values usable in :func:`create`)."""
    resp = vcfa.api_get(opts, _TOPICS, profile=profile)
    return resp.get("content", []) or []
