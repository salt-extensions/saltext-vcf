"""``firewall_rule`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_(policy, domain="default"):
    return __resource_funcs__["nsx.firewall_rule_list"](policy, domain=domain)


def get(rule, policy, domain="default"):
    return __resource_funcs__["nsx.firewall_rule_get"](rule, policy, domain=domain)


def create(rule, policy, domain="default", **spec):
    return __resource_funcs__["nsx.firewall_rule_create"](rule, policy, domain=domain, **spec)


def delete(rule, policy, domain="default"):
    return __resource_funcs__["nsx.firewall_rule_delete"](rule, policy, domain=domain)
