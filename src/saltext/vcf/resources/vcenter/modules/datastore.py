"""``datastore`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcenter.datastore_list"]()


def get(datastore):
    return __resource_funcs__["vcenter.datastore_get"](datastore)
