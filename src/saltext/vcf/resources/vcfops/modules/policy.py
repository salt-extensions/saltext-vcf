"""``policy`` module for the ``vcf_ops`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcf_ops.policy_list"]()


def get(policy_id):
    return __resource_funcs__["vcf_ops.policy_get"](policy_id)


def notification_rules_list():
    return __resource_funcs__["vcf_ops.notification_rules_list"]()
