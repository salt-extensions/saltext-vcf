"""State module for ESXi kernel module options."""

from saltext.vcf.clients import vim_host_kernel_module as c

__virtualname__ = "vcf_vim_host_kernel_module"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def options_set(name, host=None, module=None, options=None, profile=None):
    """Ensure a kernel module's option string matches *options*.

    *name* is informational; *module* defaults to *name* when omitted.
    *options* is the desired option string (e.g. ``"max_vfs=8"``).
    """
    module = module or name
    host = host or name
    ret = _ret(name)
    if options is None:
        ret["result"] = False
        ret["comment"] = "options is required"
        return ret
    current = c.get_options(__opts__, host, module, profile=profile)
    if current == options:
        ret["comment"] = f"{module} on {host} options already {options!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{module} on {host} options would change to {options!r}"
        return ret
    c.set_options(__opts__, host, module, options, profile=profile)
    ret["changes"] = {"options": (current, options)}
    ret["comment"] = f"{module} on {host} options set"
    return ret
