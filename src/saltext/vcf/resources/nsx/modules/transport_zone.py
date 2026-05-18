"""``transport_zone`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.transport_zone_list"]()


def get(zone_id):
    return __resource_funcs__["nsx.transport_zone_get"](zone_id)
