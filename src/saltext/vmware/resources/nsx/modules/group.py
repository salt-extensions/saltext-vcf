"""``group`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.group_list"]()


def get(group):
    return __resource_funcs__["nsx.group_get"](group)


def create(group, **spec):
    return __resource_funcs__["nsx.group_create"](group, **spec)


def delete(group):
    return __resource_funcs__["nsx.group_delete"](group)
