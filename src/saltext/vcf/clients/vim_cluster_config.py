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
    """Return current DRS config as a dict (incl. ``advanced_settings``)."""
    cfg = _cluster(opts, cluster, profile=profile).configurationEx.drsConfig
    return {
        "enabled": bool(cfg.enabled),
        "default_vm_behavior": (
            str(cfg.defaultVmBehavior) if cfg.defaultVmBehavior is not None else None
        ),
        "vm_monitoring_enabled": bool(getattr(cfg, "enableVmBehaviorOverrides", False)),
        "migration_threshold": int(cfg.vmotionRate) if cfg.vmotionRate is not None else None,
        "advanced_settings": {o.key: o.value for o in (getattr(cfg, "option", None) or [])},
    }


def drs_set(
    opts,
    cluster,
    enabled=None,
    default_vm_behavior=None,
    migration_threshold=None,
    vm_monitoring_enabled=None,
    advanced_settings=None,
    profile=None,
):
    """Update DRS settings. Only non-None fields are applied.

    *advanced_settings* is a ``{key: value}`` dict applied as
    ``DrsConfigInfo.option`` (``vim.OptionValue[]``).
    """
    cfg = vim.cluster.DrsConfigInfo()
    if enabled is not None:
        cfg.enabled = bool(enabled)
    if default_vm_behavior is not None:
        cfg.defaultVmBehavior = default_vm_behavior
    if migration_threshold is not None:
        cfg.vmotionRate = int(migration_threshold)
    if vm_monitoring_enabled is not None:
        cfg.enableVmBehaviorOverrides = bool(vm_monitoring_enabled)
    if advanced_settings is not None:
        cfg.option = [
            vim.option.OptionValue(key=k, value=v) for k, v in advanced_settings.items()
        ]
    spec = vim.cluster.ConfigSpecEx(drsConfig=cfg)
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# HA (das = "Distributed Availability Services")
# ---------------------------------------------------------------------------


def ha_get(opts, cluster, profile=None):
    """Return the full HA config (``vmware_cluster_ha.get`` parity)."""
    cfg = _cluster(opts, cluster, profile=profile).configurationEx.dasConfig
    out = {
        "enabled": bool(cfg.enabled),
        "host_monitoring": str(cfg.hostMonitoring),
        "vm_monitoring": str(cfg.vmMonitoring),
        "vm_component_protecting": str(getattr(cfg, "vmComponentProtecting", "disabled")),
        "admission_control_enabled": bool(getattr(cfg, "admissionControlEnabled", False)),
        "advanced_settings": {o.key: o.value for o in (getattr(cfg, "option", None) or [])},
    }
    settings = getattr(cfg, "defaultVmSettings", None)
    if settings:
        out["restart_priority"] = str(settings.restartPriority)
        out["isolation_response"] = str(settings.isolationResponse)
        if getattr(settings, "restartPriorityTimeout", None) is not None:
            out["restart_priority_timeout"] = int(settings.restartPriorityTimeout)
        tools = getattr(settings, "vmToolsMonitoringSettings", None)
        if tools is not None:
            out["vm_min_up_time"] = int(tools.minUpTime)
            out["vm_max_failure_window"] = int(tools.maxFailureWindow)
            out["vm_max_failures"] = int(tools.maxFailures)
            out["vm_failure_interval"] = int(tools.failureInterval)
        vcp = getattr(settings, "vmComponentProtectionSettings", None)
        if vcp is not None:
            out["enable_apd_timeout_for_hosts"] = bool(vcp.enableAPDTimeoutForHosts)
            out["vm_reaction_on_apd_cleared"] = str(vcp.vmReactionOnAPDCleared)
            out["vm_storage_protection_for_apd"] = str(vcp.vmStorageProtectionForAPD)
            out["vm_storage_protection_for_pdl"] = str(vcp.vmStorageProtectionForPDL)
            out["vm_terminate_delay_for_apd_sec"] = int(vcp.vmTerminateDelayForAPDSec)
    policy = getattr(cfg, "admissionControlPolicy", None)
    if policy is not None:
        out["admission_control_policy"] = _ac_policy_to_dict(policy)
    return out


def _ac_policy_to_dict(policy):
    kind = type(policy).__name__.rsplit(".", 1)[-1]
    base = {"kind": kind, "failover_level": int(policy.failoverLevel)}
    if kind == "FailoverHostAdmissionControlPolicy":
        base["failover_hosts"] = [h.name for h in (policy.failoverHosts or [])]
    elif kind == "FailoverResourcesAdmissionControlPolicy":
        base["autocompute_percentages"] = bool(policy.autoComputePercentages)
        base["cpu_failover_resources_percent"] = int(policy.cpuFailoverResourcesPercent)
        base["memory_failover_resources_percent"] = int(policy.memoryFailoverResourcesPercent)
    if getattr(policy, "resourceReductionToToleratePercent", None) is not None:
        base["resource_reduction_to_tolerate_percent"] = int(
            policy.resourceReductionToToleratePercent
        )
    return base


def _build_admission_policy(opts, policy_spec, profile=None):
    """Build ``vim.cluster.*AdmissionControlPolicy`` from a spec dict.

    Accepted shapes (first key wins)::

        {"slot_based_admission_control": {"failover_level": 1, "resource_reduction_to_tolerate_percent": 20}}
        {"failover_host_admission_control": {"failover_level": 1, "failover_hosts": ["h1"]}}
        {"reservation_based_admission_control": {"failover_level": 1, "autocompute_percentages": false,
                                                 "cpu_failover_resources_percent": 45,
                                                 "memory_failover_resources_percent": 50}}
    """
    policy = None
    if "slot_based_admission_control" in policy_spec:
        policy = vim.cluster.FailoverLevelAdmissionControlPolicy(
            failoverLevel=int(policy_spec["slot_based_admission_control"].get("failover_level", 1))
        )
    elif "failover_host_admission_control" in policy_spec:
        spec = policy_spec["failover_host_admission_control"]
        policy = vim.cluster.FailoverHostAdmissionControlPolicy(
            failoverLevel=int(spec.get("failover_level", 1))
        )
        hosts = spec.get("failover_hosts") or []
        content = soap.content(opts, profile=profile)
        resolved = []
        for host in hosts:
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.HostSystem], True
            )
            try:
                for h in container.view:
                    if host in (h._moId, h.name):  # noqa: SLF001
                        resolved.append(h)
                        break
            finally:
                container.Destroy()
        policy.failoverHosts = resolved
    elif "reservation_based_admission_control" in policy_spec:
        spec = policy_spec["reservation_based_admission_control"]
        policy = vim.cluster.FailoverResourcesAdmissionControlPolicy(
            failoverLevel=int(spec.get("failover_level", 1))
        )
        if "autocompute_percentages" in spec:
            policy.autoComputePercentages = bool(spec["autocompute_percentages"])
        if "cpu_failover_resources_percent" in spec:
            policy.cpuFailoverResourcesPercent = int(spec["cpu_failover_resources_percent"])
        if "memory_failover_resources_percent" in spec:
            policy.memoryFailoverResourcesPercent = int(spec["memory_failover_resources_percent"])
    else:
        raise ValueError(f"unknown admission control policy: {sorted(policy_spec)}")
    pct = None
    for kind in policy_spec.values():
        if isinstance(kind, dict) and "resource_reduction_to_tolerate_percent" in kind:
            pct = int(kind["resource_reduction_to_tolerate_percent"])
    if pct is not None:
        policy.resourceReductionToToleratePercent = pct
    return policy


def ha_set(
    opts,
    cluster,
    enabled=None,
    host_monitoring=None,
    vm_monitoring=None,
    restart_priority=None,
    isolation_response=None,
    admission_control_enabled=None,
    vm_component_protecting=None,
    vm_min_up_time=None,
    vm_max_failure_window=None,
    vm_max_failures=None,
    vm_failure_interval=None,
    restart_priority_timeout=None,
    enable_apd_timeout_for_hosts=None,
    vm_reaction_on_apd_cleared=None,
    vm_storage_protection_for_apd=None,
    vm_storage_protection_for_pdl=None,
    vm_terminate_delay_for_apd_sec=None,
    admission_control_policy=None,
    advanced_options=None,
    profile=None,
):
    """Update HA settings (full ``vim.cluster.ConfigSpecEx.dasConfig`` surface).

    Preserves any cluster-default VM settings that are not explicitly
    passed (no clobber).
    """
    cfg = vim.cluster.DasConfigInfo()
    if enabled is not None:
        cfg.enabled = bool(enabled)
    if host_monitoring is not None:
        cfg.hostMonitoring = host_monitoring
    if vm_monitoring is not None:
        cfg.vmMonitoring = vm_monitoring
    if vm_component_protecting is not None:
        cfg.vmComponentProtecting = vm_component_protecting
    if admission_control_enabled is not None:
        cfg.admissionControlEnabled = bool(admission_control_enabled)
    if advanced_options is not None:
        cfg.option = [vim.option.OptionValue(key=k, value=v) for k, v in advanced_options.items()]
    if admission_control_policy is not None:
        cfg.admissionControlPolicy = _build_admission_policy(
            opts, admission_control_policy, profile=profile
        )

    needs_vm_settings = any(
        v is not None
        for v in (
            restart_priority,
            isolation_response,
            restart_priority_timeout,
            vm_min_up_time,
            vm_max_failure_window,
            vm_max_failures,
            vm_failure_interval,
            enable_apd_timeout_for_hosts,
            vm_reaction_on_apd_cleared,
            vm_storage_protection_for_apd,
            vm_storage_protection_for_pdl,
            vm_terminate_delay_for_apd_sec,
        )
    )
    if needs_vm_settings:
        current = _cluster(opts, cluster, profile=profile).configurationEx.dasConfig
        current_settings = getattr(current, "defaultVmSettings", None)
        vm_settings = vim.cluster.DasVmSettings()
        # carry over current values first to avoid clobbering
        if current_settings is not None:
            vm_settings.restartPriority = current_settings.restartPriority
            vm_settings.isolationResponse = current_settings.isolationResponse
            if getattr(current_settings, "restartPriorityTimeout", None) is not None:
                vm_settings.restartPriorityTimeout = current_settings.restartPriorityTimeout
            if getattr(current_settings, "vmToolsMonitoringSettings", None) is not None:
                vm_settings.vmToolsMonitoringSettings = current_settings.vmToolsMonitoringSettings
            if getattr(current_settings, "vmComponentProtectionSettings", None) is not None:
                vm_settings.vmComponentProtectionSettings = (
                    current_settings.vmComponentProtectionSettings
                )
        if restart_priority is not None:
            vm_settings.restartPriority = restart_priority
        if isolation_response is not None:
            vm_settings.isolationResponse = isolation_response
        if restart_priority_timeout is not None:
            vm_settings.restartPriorityTimeout = int(restart_priority_timeout)
        tools = getattr(vm_settings, "vmToolsMonitoringSettings", None)
        needs_tools = any(v is not None for v in (vm_min_up_time, vm_max_failure_window,
                                                  vm_max_failures, vm_failure_interval))
        if needs_tools:
            if tools is None:
                tools = vim.cluster.VmToolsMonitoringSettings()
            if vm_monitoring is not None:
                tools.vmMonitoring = vm_monitoring
            if vm_min_up_time is not None:
                tools.minUpTime = int(vm_min_up_time)
            if vm_max_failure_window is not None:
                tools.maxFailureWindow = int(vm_max_failure_window)
            if vm_max_failures is not None:
                tools.maxFailures = int(vm_max_failures)
            if vm_failure_interval is not None:
                tools.failureInterval = int(vm_failure_interval)
            vm_settings.vmToolsMonitoringSettings = tools
        needs_vcp = any(v is not None for v in (enable_apd_timeout_for_hosts,
                                                vm_reaction_on_apd_cleared,
                                                vm_storage_protection_for_apd,
                                                vm_storage_protection_for_pdl,
                                                vm_terminate_delay_for_apd_sec))
        if needs_vcp:
            vcp = getattr(vm_settings, "vmComponentProtectionSettings", None)
            if vcp is None:
                vcp = vim.cluster.VmComponentProtectionSettings()
            if enable_apd_timeout_for_hosts is not None:
                vcp.enableAPDTimeoutForHosts = bool(enable_apd_timeout_for_hosts)
            if vm_reaction_on_apd_cleared is not None:
                vcp.vmReactionOnAPDCleared = vm_reaction_on_apd_cleared
            if vm_storage_protection_for_apd is not None:
                vcp.vmStorageProtectionForAPD = vm_storage_protection_for_apd
            if vm_storage_protection_for_pdl is not None:
                vcp.vmStorageProtectionForPDL = vm_storage_protection_for_pdl
            if vm_terminate_delay_for_apd_sec is not None:
                vcp.vmTerminateDelayForAPDSec = int(vm_terminate_delay_for_apd_sec)
            vm_settings.vmComponentProtectionSettings = vcp
        cfg.defaultVmSettings = vm_settings
    spec = vim.cluster.ConfigSpecEx(dasConfig=cfg)
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def vsan_enabled(opts, cluster, profile=None):
    """Return the cluster's vSAN enablement flag."""
    cfg = _cluster(opts, cluster, profile=profile).configurationEx
    vsan = getattr(cfg, "vsanConfigInfo", None)
    return bool(vsan.enabled) if vsan is not None else False


def get_config(opts, cluster, profile=None):
    """Aggregate DRS + HA + vSAN enablement for *cluster* (by name or MoID)."""
    out = drs_get(opts, cluster, profile=profile)
    out.update(ha_get(opts, cluster, profile=profile))
    out["vsan_enabled"] = vsan_enabled(opts, cluster, profile=profile)
    return out


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
