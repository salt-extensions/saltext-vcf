"""vSAN File Service — cluster-level enablement + file-service domains.

SOAP via ``/vsanHealth`` (``vim.cluster.VsanVcFileServiceSystem`` +
``VsanVcClusterConfigSystem``) — the same vSAN Management SDK surface
:mod:`clients.vsan_cluster` already uses for the rest of vSAN cluster
config, extended with the file-service-specific manager.
"""

from pyVmomi import vim

from saltext.vcf.utils import vsan


def enabled(opts, cluster, profile=None):
    """Return whether vSAN File Service is enabled on *cluster*."""
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    cs = vsan.cluster_config_system(opts, profile=profile)
    config = cs.VsanClusterGetConfig(cluster=obj)
    fsc = getattr(config, "fileServiceConfig", None) if config else None
    return bool(fsc and fsc.enabled)


def set_enabled(opts, cluster, enabled_, network_name=None, profile=None):
    """Enable or disable vSAN File Service on *cluster*.

    *network_name* (the FSVM management network) is required when enabling.
    Returns the reconfigure task's moId for the caller to poll with
    :func:`saltext.vcf.utils.vim.wait_for_task`.
    """
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    cs = vsan.cluster_config_system(opts, profile=profile)

    if enabled_:
        if not network_name:
            raise ValueError("network_name is required to enable vSAN File Service")
        network = _find_network(obj, network_name)
        file_service_config = vim.vsan.FileServiceConfig(enabled=True, network=network, domains=[])
    else:
        file_service_config = vim.vsan.FileServiceConfig(enabled=False)

    spec = vim.vsan.ReconfigSpec(fileServiceConfig=file_service_config)
    task = cs.VsanClusterReconfig(cluster=obj, vsanReconfigSpec=spec)
    return task._moId  # noqa: SLF001


def download_ovf(opts, cluster, ovf_url=None, profile=None):
    """Trigger the FSVM OVF download — required once before any domain can
    be created. Returns the task moId.
    """
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    fs = vsan.file_service_system(opts, profile=profile)
    url = ovf_url or fs.FindOvfDownloadUrl(obj)
    if not url:
        raise RuntimeError(f"no FSVM OVF download url found for cluster {cluster!r}")
    task = fs.DownloadFileServiceOvf(url)
    return task._moId  # noqa: SLF001


def list_domains(opts, cluster, profile=None):
    """Return the names of file service domains configured on *cluster*."""
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    fs = vsan.file_service_system(opts, profile=profile)
    domains = fs.QueryFileServiceDomains(querySpec=vim.vsan.FileServiceDomainQuerySpec(), cluster=obj)
    return [d.name for d in (domains or [])]


def domain_exists(opts, cluster, domain_name, profile=None):
    return domain_name in list_domains(opts, cluster, profile=profile)


def create_domain(
    opts,
    cluster,
    domain_name,
    ip_to_fqdn,
    subnet_mask,
    gateway_address,
    dns_suffixes,
    dns_address,
    profile=None,
):
    """Create a file service domain on *cluster*.

    *ip_to_fqdn* is ``{ip_address: fqdn}`` for each FSVM to deploy; the
    first entry becomes the primary FSVM. Returns the task moId.
    """
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    fs = vsan.file_service_system(opts, profile=profile)

    network_profiles = [
        vim.vsan.FileServiceIpConfig(
            dhcp=False,
            ipAddress=ip_address,
            subnetMask=subnet_mask,
            gateway=gateway_address,
            fqdn=fqdn,
        )
        for ip_address, fqdn in ip_to_fqdn.items()
    ]
    if network_profiles:
        network_profiles[0].isPrimary = True

    domain_config = vim.vsan.FileServiceDomainConfig(
        name=domain_name,
        dnsServerAddresses=list(dns_address),
        dnsSuffixes=list(dns_suffixes),
        fileServerIpConfig=network_profiles,
    )
    task = fs.CreateFileServiceDomain(domain_config, obj)
    return task._moId  # noqa: SLF001


def remove_domain(opts, cluster, domain_name, profile=None):
    """Remove file service domain *domain_name* from *cluster*. Returns the task moId."""
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    fs = vsan.file_service_system(opts, profile=profile)
    task = fs.RemoveFileServiceDomain(domain_name, obj)
    return task._moId  # noqa: SLF001


def _find_network(cluster_obj, network_name):
    for host in cluster_obj.host:
        for net in host.network:
            if net.name == network_name:
                return net
    raise LookupError(f"network {network_name!r} not found on any host in this cluster")
