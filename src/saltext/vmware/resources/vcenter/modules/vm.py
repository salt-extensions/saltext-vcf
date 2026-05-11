"""``vm`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["vcenter.vm_list"]()


def get(vm):
    return __resource_funcs__["vcenter.vm_get"](vm)


def power_on(vm):
    return __resource_funcs__["vcenter.vm_power_on"](vm)


def power_off(vm):
    return __resource_funcs__["vcenter.vm_power_off"](vm)


def reset(vm):
    return __resource_funcs__["vcenter.vm_reset"](vm)
