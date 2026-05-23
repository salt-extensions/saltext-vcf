"""Execution module for VCF Automation event-broker action subscriptions."""

from saltext.vcf.clients import vcfa_action_subscription as c

__virtualname__ = "vcf_vcfa_action_subscription"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all event-broker subscriptions.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_action_subscription.list_
    """
    return c.list_(__opts__, profile=profile)


def get(subscription_id, profile=None):
    """Get one subscription by id."""
    return c.get(__opts__, subscription_id, profile=profile)


def get_or_none(subscription_id, profile=None):
    """Get one subscription by id, or ``None`` on 404."""
    return c.get_or_none(__opts__, subscription_id, profile=profile)


def create(spec, profile=None):
    """Create a subscription."""
    return c.create(__opts__, spec, profile=profile)


def update(subscription_id, spec, profile=None):
    """Update a subscription."""
    return c.update(__opts__, subscription_id, spec, profile=profile)


def delete(subscription_id, profile=None):
    """Delete a subscription."""
    return c.delete(__opts__, subscription_id, profile=profile)


def list_event_topics(profile=None):
    """List every event topic the broker exposes."""
    return c.list_event_topics(__opts__, profile=profile)
