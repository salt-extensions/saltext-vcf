"""``ntp`` module for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def get():
    return __resource_funcs__["esxi.ntp_get"]()


def set_servers(servers):
    return __resource_funcs__["esxi.ntp_set_servers"](servers)


def set_enabled(enabled):
    return __resource_funcs__["esxi.ntp_set_enabled"](enabled)
