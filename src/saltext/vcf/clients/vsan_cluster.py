"""vSAN cluster configuration (SOAP via /vsanHealth)."""

from pyVmomi import vim

from saltext.vcf.utils import vsan


def get(opts, cluster, profile=None):
    """Return the cluster's vSAN config as a serializable dict.

    *cluster* is the cluster MoId (e.g. ``domain-c9``) or display name.
    Returns ``{"enabled", "dedup_compression_enabled", "encryption_enabled",
    "esa_enabled", "auto_claim_storage", "default_config", "cluster_uuid"}``.
    """
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    cfg = obj.configurationEx
    vsan_cfg = getattr(cfg, "vsanConfigInfo", None)
    if vsan_cfg is None:
        return {"enabled": False}

    cs = vsan.cluster_config_system(opts, profile=profile)
    extended = None
    try:
        extended = cs.VsanClusterGetConfig(cluster=obj)
    except vim.fault.VimFault:
        # vSAN not enabled on this cluster — fall back to basic info.
        extended = None

    out = {
        "enabled": bool(vsan_cfg.enabled),
        "auto_claim_storage": (
            bool(vsan_cfg.defaultConfig.autoClaimStorage) if vsan_cfg.defaultConfig else False
        ),
        "cluster_uuid": None,
    }
    if extended is not None:
        out["dedup_compression_enabled"] = bool(
            getattr(extended.dataEfficiencyConfig, "dedupEnabled", False)
            if getattr(extended, "dataEfficiencyConfig", None) is not None
            else False
        )
        if getattr(extended, "dataEncryptionConfig", None) is not None:
            out["encryption_enabled"] = bool(
                getattr(extended.dataEncryptionConfig, "encryptionEnabled", False)
            )
        else:
            out["encryption_enabled"] = False
        if getattr(extended, "dataInTransitEncryptionConfig", None) is not None:
            out["data_in_transit_encryption_enabled"] = bool(
                getattr(extended.dataInTransitEncryptionConfig, "enabled", False)
            )
        else:
            out["data_in_transit_encryption_enabled"] = False
        out["esa_enabled"] = bool(getattr(extended, "vsanEsaEnabled", False))
        if out["esa_enabled"]:
            # ESA has no per-cluster auto-claim toggle at all -- it always
            # claims every local disk automatically (that's the whole
            # point of ESA's disk-group-free model). The legacy
            # defaultConfig.autoClaimStorage field above is OSA-era and
            # not populated on an ESA cluster, so report the actual
            # (permanent) behavior instead of a stale/inapplicable False --
            # otherwise callers see spurious drift against a setting
            # vCenter will never let them change either way.
            out["auto_claim_storage"] = True
    return out


def reconfigure(
    opts,
    cluster,
    *,
    enabled=None,
    dedup_compression_enabled=None,
    encryption_enabled=None,
    auto_claim_storage=None,
    profile=None,
):
    """Reconfigure the cluster's vSAN settings.

    Only the fields supplied are touched; everything else is left unchanged.
    Returns a vim.Task moId for caller polling.
    """
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    cs = vsan.cluster_config_system(opts, profile=profile)

    spec = vim.vsan.ReconfigSpec()
    if enabled is not None or auto_claim_storage is not None:
        vsan_spec = vim.vsan.cluster.ConfigInfo()
        if enabled is not None:
            vsan_spec.enabled = bool(enabled)
        if auto_claim_storage is not None:
            if _is_esa(obj, cs):
                if not auto_claim_storage:
                    raise ValueError(
                        f"cluster {cluster!r} is vSAN ESA -- there is no per-cluster "
                        "auto-claim toggle to disable (ESA always claims every local "
                        "disk automatically; that's only an OSA-era setting)"
                    )
                # auto_claim_storage=True already matches ESA's permanent
                # behavior -- nothing to send. vCenter's own precheck
                # rejects HostDefaultInfo entirely on an ESA cluster
                # (com.vmware.vsan.clusterconfigprecheck.reason.notsupportedconfigsforvsanesa).
            else:
                vsan_spec.defaultConfig = vim.vsan.cluster.ConfigInfo.HostDefaultInfo()
                vsan_spec.defaultConfig.autoClaimStorage = bool(auto_claim_storage)
        spec.vsanClusterConfig = vsan_spec
    if dedup_compression_enabled is not None:
        de = vim.vsan.DataEfficiencyConfig()
        de.dedupEnabled = bool(dedup_compression_enabled)
        de.compressionEnabled = bool(dedup_compression_enabled)
        spec.dataEfficiencyConfig = de
    if encryption_enabled is not None:
        ec = vim.vsan.DataEncryptionConfig()
        ec.encryptionEnabled = bool(encryption_enabled)
        spec.dataEncryptionConfig = ec

    task = cs.VsanClusterReconfig(cluster=obj, vsanReconfigSpec=spec)
    return task._moId  # noqa: SLF001


def _is_esa(cluster_obj, cs):
    try:
        extended = cs.VsanClusterGetConfig(cluster=cluster_obj)
    except vim.fault.VimFault:
        return False
    return bool(getattr(extended, "vsanEsaEnabled", False))


def runtime_info(opts, cluster, profile=None):
    """Return runtime metrics for the vSAN cluster (capacity, perf service)."""
    obj = vsan.find_cluster(opts, cluster, profile=profile)
    cs = vsan.cluster_config_system(opts, profile=profile)
    try:
        runtime = cs.VsanClusterGetRuntimeStats(cluster=obj)
    except (vim.fault.VimFault, AttributeError):
        return {}
    return {
        "capacity_total": getattr(runtime, "totalCapacityB", None),
        "capacity_free": getattr(runtime, "freeCapacityB", None),
        "capacity_used": getattr(runtime, "usedCapacityB", None),
    }
