"""``tier0`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.tier0_list"]()


def get(tier0):
    return __resource_funcs__["nsx.tier0_get"](tier0)
