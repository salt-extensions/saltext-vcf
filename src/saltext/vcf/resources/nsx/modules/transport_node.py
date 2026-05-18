"""``transport_node`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.transport_node_list"]()


def get(node_id):
    return __resource_funcs__["nsx.transport_node_get"](node_id)
