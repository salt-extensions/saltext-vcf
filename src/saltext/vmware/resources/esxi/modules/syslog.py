"""``syslog`` module for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def get():
    return __resource_funcs__["esxi.syslog_get"]()


def set_servers(servers):
    return __resource_funcs__["esxi.syslog_set_servers"](servers)


def set_log_level(level):
    return __resource_funcs__["esxi.syslog_set_log_level"](level)
