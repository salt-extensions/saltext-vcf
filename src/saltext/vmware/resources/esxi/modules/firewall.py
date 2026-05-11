"""``firewall`` module for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def list_():
    return __resource_funcs__["esxi.firewall_list"]()


def get(rule):
    return __resource_funcs__["esxi.firewall_get"](rule)


def set_enabled(rule, enabled):
    return __resource_funcs__["esxi.firewall_set_enabled"](rule, enabled)


def set_allowed_ips(rule, allowed_ips, all_ip=False):
    return __resource_funcs__["esxi.firewall_set_allowed_ips"](rule, allowed_ips, all_ip=all_ip)
