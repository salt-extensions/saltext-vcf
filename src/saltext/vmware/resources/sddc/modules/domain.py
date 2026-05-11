"""``domain`` module for the ``sddc`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["sddc.domain_list"]()


def get(domain):
    return __resource_funcs__["sddc.domain_get"](domain)
