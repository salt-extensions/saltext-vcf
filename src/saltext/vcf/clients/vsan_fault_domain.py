"""vSAN fault domain configuration (SOAP).

Fault domains group hosts that share a failure boundary (rack, power
domain, blade chassis). vSAN places replica copies across FDs so the
loss of an entire FD doesn't take data offline. Fault domains are
mandatory in stretched-cluster topologies.

Reconfigured via the cluster vSAN reconfig API with a
``vim.cluster.VsanFaultDomainsConfigSpec`` containing a list of
``vim.cluster.VsanFaultDomainSpec`` (name + member hosts).
"""

from pyVmomi import vim

from saltext.vcf.utils import vsan


def list_(opts, cluster, profile=None):
    """Return current fault-domain assignments for *cluster*.

    Each ESXi host carries its own ``faultDomainInfo`` on
    ``host.configManager.vsanSystem.config``. VCF 9.x's
    ``VsanClusterGetConfig`` does not return the per-host array, so we
    iterate the cluster's member hosts directly.

    Output: a list of ``{"host", "host_id", "fault_domain", "node_uuid"}``
    dicts — one per host in the cluster. ``fault_domain`` is None when
    the host is not in any FD.
    """
    cluster_obj = vsan.find_cluster(opts, cluster, profile=profile)
    out = []
    for host in cluster_obj.host:
        vsan_system = host.configManager.vsanSystem
        cfg = vsan_system.config if vsan_system else None
        fd_info = getattr(cfg, "faultDomainInfo", None) if cfg else None
        cluster_info = getattr(cfg, "clusterInfo", None) if cfg else None
        out.append(
            {
                "host": host.name,
                "host_id": host._moId,  # noqa: SLF001
                "fault_domain": fd_info.name if fd_info and fd_info.name else None,
                "node_uuid": cluster_info.nodeUuid if cluster_info else None,
            }
        )
    return out


def assign(opts, cluster, mapping, profile=None):
    """Assign hosts to fault domains.

    *mapping* is a dict ``{host_id_or_name: fault_domain_name}``. Hosts
    referenced by name OR MoId are resolved against the cluster's member
    list. Hosts not present in the cluster are silently ignored.

    Returns the vim.Task moId.
    """
    cluster_obj = vsan.find_cluster(opts, cluster, profile=profile)
    cs = vsan.cluster_config_system(opts, profile=profile)

    # Group hosts by their target fault-domain name
    by_fd: dict[str, list] = {}
    for host in cluster_obj.host:
        target = mapping.get(host.name) or mapping.get(host._moId)  # noqa: SLF001
        if target is None:
            continue
        by_fd.setdefault(target, []).append(host)

    fd_specs = []
    for fd_name, hosts in by_fd.items():
        fd_spec = vim.cluster.VsanFaultDomainSpec()
        fd_spec.name = fd_name
        fd_spec.hosts = hosts
        fd_specs.append(fd_spec)

    fds_config = vim.cluster.VsanFaultDomainsConfigSpec()
    fds_config.faultDomains = fd_specs

    spec = vim.vsan.ReconfigSpec()
    spec.faultDomainsSpec = fds_config

    task = cs.VsanClusterReconfig(cluster=cluster_obj, vsanReconfigSpec=spec)
    return task._moId  # noqa: SLF001
