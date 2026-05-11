"""``datacenter`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcenter.datacenter_list"]()


def get(datacenter):
    return __resource_funcs__["vcenter.datacenter_get"](datacenter)


def create(name, folder=None):
    return __resource_funcs__["vcenter.datacenter_create"](name, folder=folder)


def delete(datacenter):
    return __resource_funcs__["vcenter.datacenter_delete"](datacenter)
