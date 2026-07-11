"""Execution module for VCF Operations outbound webhooks and notification rules."""

from saltext.vcf.clients import vcfops_webhook as c

__virtualname__ = "vcf_vcfops_webhook"


def __virtual__():
    return __virtualname__


# ---------------------------------------------------------------------------
# Outbound instances
# ---------------------------------------------------------------------------


def list_(page=0, page_size=1000, profile=None):
    """List every configured outbound webhook / notification instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.list_
    """
    return c.list_(__opts__, page=page, page_size=page_size, profile=profile)


def get(instance_id, profile=None):
    """Return the outbound instance with id *instance_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.get <instance-id>
    """
    return c.get(__opts__, instance_id, profile=profile)


def get_or_none(instance_id, profile=None):
    """Like :func:`get` but returns ``None`` on a 404.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.get_or_none <instance-id>
    """
    return c.get_or_none(__opts__, instance_id, profile=profile)


def create(instance_spec, profile=None):
    """Create an outbound webhook / notification instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.create '{"name": "pd", "pluginTypeId": "RestPlugin", ...}'
    """
    return c.create(__opts__, instance_spec, profile=profile)


def update(instance_id, instance_spec, profile=None):
    """Replace an outbound instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.update <instance-id> '{...}'
    """
    return c.update(__opts__, instance_id, instance_spec, profile=profile)


def delete(instance_id, profile=None):
    """Delete an outbound instance by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.delete <instance-id>
    """
    return c.delete(__opts__, instance_id, profile=profile)


# ---------------------------------------------------------------------------
# Notification rules
# ---------------------------------------------------------------------------


def list_rules(page=0, page_size=1000, profile=None):
    """List every notification rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.list_rules
    """
    return c.list_rules(__opts__, page=page, page_size=page_size, profile=profile)


def get_rule(rule_id, profile=None):
    """Return the notification rule with id *rule_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.get_rule <rule-id>
    """
    return c.get_rule(__opts__, rule_id, profile=profile)


def get_rule_or_none(rule_id, profile=None):
    """Like :func:`get_rule` but returns ``None`` on a 404.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.get_rule_or_none <rule-id>
    """
    return c.get_rule_or_none(__opts__, rule_id, profile=profile)


def create_rule(rule_spec, profile=None):
    """Create a notification rule binding an alert to an outbound instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.create_rule '{"name": "...", "pluginId": "...", ...}'
    """
    return c.create_rule(__opts__, rule_spec, profile=profile)


def update_rule(rule_id, rule_spec, profile=None):
    """Replace a notification rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.update_rule <rule-id> '{...}'
    """
    return c.update_rule(__opts__, rule_id, rule_spec, profile=profile)


def delete_rule(rule_id, profile=None):
    """Delete a notification rule by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_webhook.delete_rule <rule-id>
    """
    return c.delete_rule(__opts__, rule_id, profile=profile)
