"""``host`` module for the ``sddc`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["sddc.host_list"]()


def get(host):
    return __resource_funcs__["sddc.host_get"](host)


def commission(host_specs):
    return __resource_funcs__["sddc.host_commission"](host_specs)


def decommission(host):
    return __resource_funcs__["sddc.host_decommission"](host)
