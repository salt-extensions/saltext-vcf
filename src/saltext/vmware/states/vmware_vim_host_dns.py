"""State module for ESXi host DNS config."""

from saltext.vmware.clients import vim_host_dns as c

__virtualname__ = "vmware_vim_host_dns"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def config(
    name,
    host=None,
    dhcp=None,
    hostname=None,
    domain_name=None,
    servers=None,
    search_domains=None,
    profile=None,
):
    """Ensure DNS config on *host* matches the supplied fields.

    *host* defaults to *name*. None values are not checked.
    """
    host = host or name
    ret = _ret(name)
    current = c.get(__opts__, host, profile=profile)
    drift = {}
    if dhcp is not None and current["dhcp"] != bool(dhcp):
        drift["dhcp"] = (current["dhcp"], bool(dhcp))
    if hostname is not None and current["hostname"] != hostname:
        drift["hostname"] = (current["hostname"], hostname)
    if domain_name is not None and current["domain_name"] != domain_name:
        drift["domain_name"] = (current["domain_name"], domain_name)
    if servers is not None and sorted(current["servers"]) != sorted(servers):
        drift["servers"] = (current["servers"], list(servers))
    if search_domains is not None and sorted(current["search_domains"]) != sorted(search_domains):
        drift["search_domains"] = (current["search_domains"], list(search_domains))
    if not drift:
        ret["comment"] = f"DNS on {host} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DNS on {host} would change: {sorted(drift)}"
        return ret
    c.set_(
        __opts__,
        host,
        dhcp=dhcp,
        hostname=hostname,
        domain_name=domain_name,
        servers=servers,
        search_domains=search_domains,
        profile=profile,
    )
    ret["changes"] = drift
    ret["comment"] = f"DNS on {host} updated"
    return ret
