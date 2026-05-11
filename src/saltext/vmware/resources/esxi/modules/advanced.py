"""``advanced`` module for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["esxi.advanced_list"]()


def get(key):
    return __resource_funcs__["esxi.advanced_get"](key)


def set_value(key, value):
    return __resource_funcs__["esxi.advanced_set"](key, value)
