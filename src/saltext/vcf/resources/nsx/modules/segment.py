"""``segment`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.segment_list"]()


def get(segment):
    return __resource_funcs__["nsx.segment_get"](segment)


def create(segment, **spec):
    return __resource_funcs__["nsx.segment_create"](segment, **spec)


def delete(segment):
    return __resource_funcs__["nsx.segment_delete"](segment)
