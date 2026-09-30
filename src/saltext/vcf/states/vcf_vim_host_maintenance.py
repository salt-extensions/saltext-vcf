"""State module for ESXi host maintenance mode (vCenter-routed SOAP)."""

from saltext.vcf.clients import vim_host_maintenance as c

__virtualname__ = "vcf_vim_host_maintenance"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def maintenance(
    name,
    host,
    enter_maintenance_mode=True,
    timeout=0,
    evacuate_powered_off_vms=False,
    vsan_mode=None,
    profile=None,
):
    """Ensure the host is in (or out of) maintenance mode.

    .. code-block:: yaml

        Maintenance mode:
          vcf_vim_host_maintenance.maintenance:
            - host: esxi-01
            - enter_maintenance_mode: true
    """
    ret = _ret(name)
    is_in = c.is_in(__opts__, host, profile=profile)
    if bool(is_in) == bool(enter_maintenance_mode):
        ret["comment"] = (
            f"Host {host} already in maintenance mode."
            if is_in
            else f"Host {host} already out of maintenance mode."
        )
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = (
            f"Host {host} would enter maintenance mode."
            if enter_maintenance_mode
            else f"Host {host} would exit maintenance mode."
        )
        ret["changes"] = {"maintenance": (is_in, bool(enter_maintenance_mode))}
        return ret
    if enter_maintenance_mode:
        c.enter(
            __opts__,
            host,
            evacuate_powered_off_vms=evacuate_powered_off_vms,
            vsan_mode=vsan_mode,
            timeout=timeout,
            profile=profile,
        )
    else:
        c.exit_(__opts__, host, timeout=timeout, profile=profile)
    ret["changes"] = {"maintenance": (is_in, bool(enter_maintenance_mode))}
    ret["comment"] = f"Host {host} maintenance mode updated."
    return ret
