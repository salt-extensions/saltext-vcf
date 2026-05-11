"""``node`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def get():
    return __resource_funcs__["nsx.node_info"]()
