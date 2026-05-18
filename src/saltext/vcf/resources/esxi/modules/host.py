"""``host`` module for the ``esxi`` resource type."""

# pylint: disable=undefined-variable


def info():
    return __resource_funcs__["esxi.host_info"]()


def lockdown_get():
    return __resource_funcs__["esxi.host_lockdown_get"]()


def lockdown_set(mode, exception_users=None):
    return __resource_funcs__["esxi.host_lockdown_set"](mode, exception_users=exception_users)


def enter_maintenance():
    return __resource_funcs__["esxi.host_enter_maintenance"]()


def exit_maintenance():
    return __resource_funcs__["esxi.host_exit_maintenance"]()


def reboot(force=False):
    return __resource_funcs__["esxi.host_reboot"](force=force)


def shutdown(force=False):
    return __resource_funcs__["esxi.host_shutdown"](force=force)
