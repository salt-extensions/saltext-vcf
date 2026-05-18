"""``security_policy`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_(domain="default"):
    return __resource_funcs__["nsx.security_policy_list"](domain=domain)


def get(policy, domain="default"):
    return __resource_funcs__["nsx.security_policy_get"](policy, domain=domain)


def create(policy, domain="default", **spec):
    return __resource_funcs__["nsx.security_policy_create"](policy, domain=domain, **spec)


def delete(policy, domain="default"):
    return __resource_funcs__["nsx.security_policy_delete"](policy, domain=domain)
