"""``service`` module for the ``nsx`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["nsx.service_list"]()


def get(service):
    return __resource_funcs__["nsx.service_get"](service)


def create(service, **spec):
    return __resource_funcs__["nsx.service_create"](service, **spec)


def delete(service):
    return __resource_funcs__["nsx.service_delete"](service)
