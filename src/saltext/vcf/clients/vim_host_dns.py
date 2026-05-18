"""ESXi host DNS / hostname config via ``HostNetworkSystem`` (SOAP)."""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for host in container.view:
            if host_id_or_name in (host._moId, host.name):  # noqa: SLF001
                return host
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


def _net(host):
    n = host.configManager.networkSystem
    if n is None:
        raise RuntimeError(f"host {host.name!r} has no networkSystem manager")
    return n


def get(opts, host, profile=None):
    """Return ``{dhcp, hostname, domain_name, servers, search_domains, virtual_nic}``."""
    h = _host(opts, host, profile=profile)
    cfg = h.config.network.dnsConfig
    return {
        "dhcp": bool(cfg.dhcp),
        "hostname": cfg.hostName,
        "domain_name": cfg.domainName,
        "servers": list(cfg.address or []),
        "search_domains": list(cfg.searchDomain or []),
        "virtual_nic": cfg.virtualNicDevice or None,
    }


def set_(
    opts,
    host,
    *,
    dhcp=None,
    hostname=None,
    domain_name=None,
    servers=None,
    search_domains=None,
    virtual_nic=None,
    profile=None,
):
    """Update the host's DNS config. Any None argument leaves the current value alone."""
    h = _host(opts, host, profile=profile)
    cur = h.config.network.dnsConfig
    spec = vim.host.DnsConfig()
    spec.dhcp = bool(cur.dhcp) if dhcp is None else bool(dhcp)
    spec.hostName = cur.hostName if hostname is None else hostname
    spec.domainName = cur.domainName if domain_name is None else domain_name
    spec.address = list(cur.address or []) if servers is None else list(servers)
    spec.searchDomain = (
        list(cur.searchDomain or []) if search_domains is None else list(search_domains)
    )
    if virtual_nic is not None:
        spec.virtualNicDevice = virtual_nic
    elif cur.virtualNicDevice:
        spec.virtualNicDevice = cur.virtualNicDevice
    _net(h).UpdateDnsConfig(config=spec)
    return get(opts, host, profile=profile)
