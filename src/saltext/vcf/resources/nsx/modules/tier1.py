"""``tier1`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.tier1_list"]()


def get(tier1):
    return __resource_funcs__["nsx.tier1_get"](tier1)


def create(tier1, **spec):
    return __resource_funcs__["nsx.tier1_create"](tier1, **spec)


def delete(tier1):
    return __resource_funcs__["nsx.tier1_delete"](tier1)
