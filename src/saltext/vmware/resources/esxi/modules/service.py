"""``service`` module for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["esxi.service_list"]()


def get(service):
    return __resource_funcs__["esxi.service_get"](service)


def start(service):
    return __resource_funcs__["esxi.service_start"](service)


def stop(service):
    return __resource_funcs__["esxi.service_stop"](service)


def restart(service):
    return __resource_funcs__["esxi.service_restart"](service)


def set_policy(service, policy):
    return __resource_funcs__["esxi.service_set_policy"](service, policy)
