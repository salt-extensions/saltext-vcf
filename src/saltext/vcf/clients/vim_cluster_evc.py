"""Cluster EVC (Enhanced vMotion Compatibility) mode."""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _cluster(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if not isinstance(dc, vim.Datacenter):
            continue
        for entity in dc.hostFolder.childEntity:
            if isinstance(entity, vim.ClusterComputeResource) and name_or_id in (
                entity._moId,  # noqa: SLF001
                entity.name,
            ):
                return entity
    raise LookupError(f"cluster {name_or_id!r} not found")


def _evc_mgr(cluster):
    mgr = cluster.EvcManager()
    if mgr is None:
        raise RuntimeError(f"cluster {cluster.name!r} has no EVC manager")
    return mgr


def get(opts, cluster, profile=None):
    """Return ``{enabled, current_key, supported_keys, feature_capabilities}``."""
    cl = _cluster(opts, cluster, profile=profile)
    mgr = _evc_mgr(cl)
    state = mgr.evcState
    return {
        "enabled": bool(state.currentEVCModeKey),
        "current_key": state.currentEVCModeKey,
        "supported_keys": [m.key for m in (state.supportedEVCMode or [])],
        "guaranteed_cpu_features": [
            {"key": f.key, "value": f.value} for f in (state.guaranteedCPUFeatures or [])
        ],
    }


def configure(opts, cluster, evc_mode_key, profile=None):
    """Enable or change EVC mode on *cluster*. Returns the vim.Task moId."""
    cl = _cluster(opts, cluster, profile=profile)
    mgr = _evc_mgr(cl)
    task = mgr.ConfigureEvcMode_Task(evcModeKey=evc_mode_key)
    return task._moId  # noqa: SLF001


def disable(opts, cluster, profile=None):
    """Disable EVC mode on *cluster*. Returns the vim.Task moId."""
    cl = _cluster(opts, cluster, profile=profile)
    mgr = _evc_mgr(cl)
    task = mgr.DisableEvcMode_Task()
    return task._moId  # noqa: SLF001


def check(opts, cluster, evc_mode_key, profile=None):
    """Dry-run check whether *evc_mode_key* can be applied. Returns the vim.Task moId."""
    cl = _cluster(opts, cluster, profile=profile)
    mgr = _evc_mgr(cl)
    task = mgr.CheckConfigureEvcMode_Task(evcModeKey=evc_mode_key)
    return task._moId  # noqa: SLF001
