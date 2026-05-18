"""``storage_policy`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcenter.storage_policy_list"]()


def get(policy):
    return __resource_funcs__["vcenter.storage_policy_get"](policy)
