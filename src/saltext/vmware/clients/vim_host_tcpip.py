"""ESXi TCP/IP stack config via ``HostNetworkSystem.netStackInstance``.

Common stacks: ``defaultTcpipStack``, ``vmotion``, ``vSphereProvisioning``.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def _host(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for h in container.view:
            if name_or_id in (h._moId, h.name):  # noqa: SLF001
                return h
    finally:
        container.Destroy()
    raise LookupError(f"host {name_or_id!r} not found")


def _net(host):
    n = host.configManager.networkSystem
    if n is None:
        raise RuntimeError(f"host {host.name!r} has no networkSystem manager")
    return n


def _to_dict(stack):
    # pyVmomi exposes default gateways only after a full route-table walk via
    # the host's IP route info (separate manager call); we expose the bits
    # that are reachable directly from the NetStackInstance config.
    return {
        "key": stack.key,
        "name": stack.name,
        "dns_config": (
            {
                "hostname": stack.dnsConfig.hostName if stack.dnsConfig else None,
                "domain": stack.dnsConfig.domainName if stack.dnsConfig else None,
                "servers": list(stack.dnsConfig.address or []) if stack.dnsConfig else [],
                "search": list(stack.dnsConfig.searchDomain or []) if stack.dnsConfig else [],
            }
            if stack.dnsConfig
            else None
        ),
        "ipv6_enabled": bool(getattr(stack, "ipV6Enabled", False)),
    }


def list_(opts, host, profile=None):
    """Return every TCP/IP stack instance on *host*."""
    h = _host(opts, host, profile=profile)
    return [_to_dict(s) for s in (h.config.network.netStackInstance or [])]


def get(opts, host, stack_key, profile=None):
    for s in list_(opts, host, profile=profile):
        if s["key"] == stack_key:
            return s
    raise LookupError(f"TCP/IP stack {stack_key!r} not found on host {host!r}")


def get_or_none(opts, host, stack_key, profile=None):
    try:
        return get(opts, host, stack_key, profile=profile)
    except LookupError:
        return None


def update(
    opts,
    host,
    stack_key,
    *,
    dns_servers=None,
    dns_search_domains=None,
    profile=None,
):
    """Update DNS settings on a named TCP/IP stack. None args are not touched.

    Default-gateway changes require authoring the full ``IpRoute`` list and
    are intentionally not exposed here — use ESXCLI for route table changes.
    """
    h = _host(opts, host, profile=profile)
    cur = None
    for s in h.config.network.netStackInstance or []:
        if s.key == stack_key:
            cur = s
            break
    if cur is None:
        raise LookupError(f"TCP/IP stack {stack_key!r} not found")
    spec = vim.host.NetStackInstance()
    spec.key = stack_key
    spec.name = cur.name
    if dns_servers is not None or dns_search_domains is not None:
        dns = vim.host.DnsConfig()
        old = cur.dnsConfig
        dns.dhcp = bool(old.dhcp) if old else False
        dns.hostName = old.hostName if old else ""
        dns.domainName = old.domainName if old else ""
        dns.address = (
            list(dns_servers) if dns_servers is not None else list(old.address or [] if old else [])
        )
        dns.searchDomain = (
            list(dns_search_domains)
            if dns_search_domains is not None
            else list(old.searchDomain or [] if old else [])
        )
        spec.dnsConfig = dns
    _net(h).UpdateNetStackInstance(netStackInstance=spec)
    return get(opts, host, stack_key, profile=profile)
