"""``host`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcenter.host_list"]()


def get(host):
    return __resource_funcs__["vcenter.host_get"](host)


def enter_maintenance(host):
    return __resource_funcs__["vcenter.host_enter_maintenance"](host)


def exit_maintenance(host):
    return __resource_funcs__["vcenter.host_exit_maintenance"](host)
