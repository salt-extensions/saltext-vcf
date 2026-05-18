"""Cluster-level DRS / HA / EVC / DPM settings via SOAP.

DRS rules + VM/host groups live in ``vim_drs_rule``. This module
manages the cluster-wide *behavior* knobs: whether DRS is on, what
automation level, HA tolerations, EVC mode, etc.

All writes go through ``ClusterComputeResource.ReconfigureComputeResource_Task``
with a ``vim.cluster.ConfigSpecEx`` carrying the relevant sub-spec.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _cluster(opts, name, profile=None):
    content = soap.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if not isinstance(dc, vim.Datacenter):
            continue
        for entity in dc.hostFolder.childEntity:
            if isinstance(entity, vim.ClusterComputeResource) and name in (
                entity._moId,  # noqa: SLF001
                entity.name,
            ):
                return entity
    raise LookupError(f"cluster {name!r} not found")


# ---------------------------------------------------------------------------
# DRS
# ---------------------------------------------------------------------------


def drs_get(opts, cluster, profile=None):
    """Return current DRS config as a dict."""
    cfg = _cluster(opts, cluster, profile=profile).configurationEx.drsConfig
    return {
        "enabled": bool(cfg.enabled),
        "default_vm_behavior": str(cfg.defaultVmBehavior),
        "vm_monitoring_enabled": bool(getattr(cfg, "enableVmBehaviorOverrides", False)),
        "migration_threshold": int(cfg.vmotionRate),
    }


def drs_set(
    opts,
    cluster,
    enabled=None,
    default_vm_behavior=None,
    migration_threshold=None,
    vm_monitoring_enabled=None,
    profile=None,
):
    """Update DRS settings. Only non-None fields are applied."""
    cfg = vim.cluster.DrsConfigInfo()
    if enabled is not None:
        cfg.enabled = bool(enabled)
    if default_vm_behavior is not None:
        cfg.defaultVmBehavior = default_vm_behavior
    if migration_threshold is not None:
        cfg.vmotionRate = int(migration_threshold)
    if vm_monitoring_enabled is not None:
        cfg.enableVmBehaviorOverrides = bool(vm_monitoring_enabled)
    spec = vim.cluster.ConfigSpecEx(drsConfig=cfg)
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# HA (das = "Distributed Availability Services")
# ---------------------------------------------------------------------------


def ha_get(opts, cluster, profile=None):
    cfg = _cluster(opts, cluster, profile=profile).configurationEx.dasConfig
    out = {
        "enabled": bool(cfg.enabled),
        "host_monitoring": str(cfg.hostMonitoring),
        "vm_monitoring": str(cfg.vmMonitoring),
        "admission_control_enabled": bool(getattr(cfg, "admissionControlEnabled", False)),
    }
    if cfg.defaultVmSettings:
        out["restart_priority"] = str(cfg.defaultVmSettings.restartPriority)
        out["isolation_response"] = str(cfg.defaultVmSettings.isolationResponse)
    return out


def ha_set(
    opts,
    cluster,
    enabled=None,
    host_monitoring=None,
    vm_monitoring=None,
    restart_priority=None,
    isolation_response=None,
    admission_control_enabled=None,
    profile=None,
):
    """Update HA settings."""
    cfg = vim.cluster.DasConfigInfo()
    if enabled is not None:
        cfg.enabled = bool(enabled)
    if host_monitoring is not None:
        cfg.hostMonitoring = host_monitoring
    if vm_monitoring is not None:
        cfg.vmMonitoring = vm_monitoring
    if admission_control_enabled is not None:
        cfg.admissionControlEnabled = bool(admission_control_enabled)
    if restart_priority is not None or isolation_response is not None:
        vm_settings = vim.cluster.DasVmSettings()
        if restart_priority is not None:
            vm_settings.restartPriority = restart_priority
        if isolation_response is not None:
            vm_settings.isolationResponse = isolation_response
        cfg.defaultVmSettings = vm_settings
    spec = vim.cluster.ConfigSpecEx(dasConfig=cfg)
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# EVC (Enhanced vMotion Compatibility) — separate API on the cluster
# ---------------------------------------------------------------------------


def evc_get(opts, cluster, profile=None):
    """Return the EVC mode and supported baselines."""
    cl = _cluster(opts, cluster, profile=profile)
    summary = cl.summary
    return {
        "current_mode": getattr(summary, "currentEVCModeKey", None),
        "current_graphics_mode": getattr(summary, "currentEVCGraphicsModeKey", None),
    }


def evc_set(opts, cluster, mode, profile=None):
    """Configure (or enable) cluster EVC at *mode* (e.g. ``intel-skylake``).

    Uses ``EvcManager.ConfigureEvcMode_Task``.
    """
    cl = _cluster(opts, cluster, profile=profile)
    evc_mgr = cl.EvcManager()
    task = evc_mgr.ConfigureEvcMode_Task(evcModeKey=mode)
    return task._moId  # noqa: SLF001


def evc_disable(opts, cluster, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    evc_mgr = cl.EvcManager()
    task = evc_mgr.DisableEvcMode_Task()
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# DPM (Distributed Power Management) — part of DRS config block on cluster
# ---------------------------------------------------------------------------


def dpm_get(opts, cluster, profile=None):
    cfg = _cluster(opts, cluster, profile=profile).configurationEx.dpmConfigInfo
    if cfg is None:
        return {"enabled": False, "default_behavior": None, "host_power_action_rate": None}
    return {
        "enabled": bool(cfg.enabled),
        "default_behavior": str(cfg.defaultDpmBehavior),
        "host_power_action_rate": int(cfg.hostPowerActionRate),
    }


def dpm_set(
    opts, cluster, enabled=None, default_behavior=None, host_power_action_rate=None, profile=None
):
    cfg = vim.cluster.DpmConfigInfo()
    if enabled is not None:
        cfg.enabled = bool(enabled)
    if default_behavior is not None:
        cfg.defaultDpmBehavior = default_behavior
    if host_power_action_rate is not None:
        cfg.hostPowerActionRate = int(host_power_action_rate)
    spec = vim.cluster.ConfigSpecEx(dpmConfig=cfg)
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001
