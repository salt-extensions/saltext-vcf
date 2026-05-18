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


def search(
    power_states=None,
    names=None,
    hosts=None,
    clusters=None,
    folders=None,
    datacenters=None,
    resource_pools=None,
    vms=None,
):
    return __resource_funcs__["vcenter.vm_search"](
        power_states=power_states,
        names=names,
        hosts=hosts,
        clusters=clusters,
        folders=folders,
        datacenters=datacenters,
        resource_pools=resource_pools,
        vms=vms,
    )


def tree():
    return __resource_funcs__["vcenter.vm_tree"]()


def summary():
    return __resource_funcs__["vcenter.vm_summary"]()
