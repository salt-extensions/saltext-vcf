"""``credentials`` module for the ``sddc`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["sddc.credentials_list"]()


def rotate(elements):
    return __resource_funcs__["sddc.credentials_rotate"](elements)
