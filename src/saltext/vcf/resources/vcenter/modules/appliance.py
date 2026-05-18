"""``appliance`` module for the ``vcenter`` resource type."""

# pylint: disable=undefined-variable


def services_list():
    return __resource_funcs__["vcenter.appliance_services_list"]()


def services_get(service):
    return __resource_funcs__["vcenter.appliance_services_get"](service)


def services_start(service):
    return __resource_funcs__["vcenter.appliance_services_start"](service)


def services_stop(service):
    return __resource_funcs__["vcenter.appliance_services_stop"](service)


def services_restart(service):
    return __resource_funcs__["vcenter.appliance_services_restart"](service)


def version():
    return __resource_funcs__["vcenter.appliance_version"]()


def health_system():
    return __resource_funcs__["vcenter.appliance_health_system"]()


def dns_get():
    return __resource_funcs__["vcenter.appliance_dns_get"]()


def dns_set(servers, mode="is_static"):
    return __resource_funcs__["vcenter.appliance_dns_set"](servers, mode=mode)


def logging_forwarding_get():
    return __resource_funcs__["vcenter.appliance_logging_forwarding_get"]()


def logging_forwarding_set(servers):
    return __resource_funcs__["vcenter.appliance_logging_forwarding_set"](servers)
