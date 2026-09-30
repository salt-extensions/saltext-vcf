"""Tests for clients.vim_cluster_config (DRS / HA / EVC / DPM via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_cluster_config


def _fake_cluster(drs=None, das=None, dpm=None, summary=None):
    cl = MagicMock()
    drs_cfg = vim.cluster.DrsConfigInfo() if drs is None else drs
    cl.configurationEx.drsConfig = drs_cfg
    das_cfg = vim.cluster.DasConfigInfo() if das is None else das
    cl.configurationEx.dasConfig = das_cfg
    cl.configurationEx.dpmConfigInfo = dpm
    cl.summary = summary or MagicMock(currentEVCModeKey=None, currentEVCGraphicsModeKey=None)
    cl.ReconfigureComputeResource_Task.return_value = MagicMock(_moId="task-1")
    evc_mgr = MagicMock()
    evc_mgr.ConfigureEvcMode_Task.return_value = MagicMock(_moId="evc-task-1")
    evc_mgr.DisableEvcMode_Task.return_value = MagicMock(_moId="evc-task-2")
    cl.EvcManager.return_value = evc_mgr
    return cl


@pytest.fixture
def cluster_factory(monkeypatch):
    holder = {"cluster": _fake_cluster()}
    monkeypatch.setattr(
        vim_cluster_config, "_cluster", lambda opts, name, profile=None: holder["cluster"]
    )
    return holder


# ---------- DRS ----------


def test_drs_get_returns_dict(cluster_factory, opts):
    drs = vim.cluster.DrsConfigInfo()
    drs.enabled = True
    drs.defaultVmBehavior = "fullyAutomated"
    drs.vmotionRate = 3
    drs.enableVmBehaviorOverrides = True
    cluster_factory["cluster"] = _fake_cluster(drs=drs)
    result = vim_cluster_config.drs_get(opts, "domain-c9")
    assert result == {
        "enabled": True,
        "default_vm_behavior": "fullyAutomated",
        "vm_monitoring_enabled": True,
        "migration_threshold": 3,
        "advanced_settings": {},
    }


def test_drs_set_only_passes_non_none(cluster_factory, opts):
    vim_cluster_config.drs_set(opts, "domain-c9", enabled=True, migration_threshold=4)
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.drsConfig.enabled is True
    assert spec.drsConfig.vmotionRate == 4
    # default_vm_behavior wasn't passed; the field stays unset (None)
    assert spec.drsConfig.defaultVmBehavior is None


# ---------- HA ----------


def test_ha_get_includes_vm_settings(cluster_factory, opts):
    das = vim.cluster.DasConfigInfo()
    das.enabled = True
    das.hostMonitoring = "enabled"
    das.vmMonitoring = "vmMonitoringOnly"
    das.admissionControlEnabled = True
    vm_settings = vim.cluster.DasVmSettings()
    vm_settings.restartPriority = "high"
    vm_settings.isolationResponse = "shutdown"
    das.defaultVmSettings = vm_settings
    cluster_factory["cluster"] = _fake_cluster(das=das)
    result = vim_cluster_config.ha_get(opts, "domain-c9")
    assert result["enabled"] is True
    assert result["host_monitoring"] == "enabled"
    assert result["vm_monitoring"] == "vmMonitoringOnly"
    assert result["restart_priority"] == "high"
    assert result["isolation_response"] == "shutdown"
    assert result["admission_control_enabled"] is True


def test_ha_set_packs_vm_settings(cluster_factory, opts):
    vim_cluster_config.ha_set(
        opts,
        "domain-c9",
        enabled=True,
        restart_priority="high",
        isolation_response="shutdown",
    )
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.dasConfig.enabled is True
    assert spec.dasConfig.defaultVmSettings.restartPriority == "high"
    assert spec.dasConfig.defaultVmSettings.isolationResponse == "shutdown"


def test_ha_set_skips_vm_settings_when_no_overrides(cluster_factory, opts):
    vim_cluster_config.ha_set(opts, "domain-c9", enabled=True)
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.dasConfig.defaultVmSettings is None


# ---------- EVC ----------


def test_evc_get(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(
        summary=MagicMock(currentEVCModeKey="intel-skylake", currentEVCGraphicsModeKey=None)
    )
    result = vim_cluster_config.evc_get(opts, "domain-c9")
    assert result["current_mode"] == "intel-skylake"


def test_evc_set_invokes_configure_task(cluster_factory, opts):
    vim_cluster_config.evc_set(opts, "domain-c9", "intel-skylake")
    cluster_factory[
        "cluster"
    ].EvcManager.return_value.ConfigureEvcMode_Task.assert_called_once_with(
        evcModeKey="intel-skylake"
    )


def test_evc_disable_invokes_disable_task(cluster_factory, opts):
    vim_cluster_config.evc_disable(opts, "domain-c9")
    cluster_factory["cluster"].EvcManager.return_value.DisableEvcMode_Task.assert_called_once()


# ---------- DPM ----------


def test_dpm_get_none_returns_disabled(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(dpm=None)
    result = vim_cluster_config.dpm_get(opts, "domain-c9")
    assert result == {
        "enabled": False,
        "default_behavior": None,
        "host_power_action_rate": None,
    }


def test_dpm_get_returns_populated(cluster_factory, opts):
    dpm = vim.cluster.DpmConfigInfo()
    dpm.enabled = True
    dpm.defaultDpmBehavior = "automated"
    dpm.hostPowerActionRate = 4
    cluster_factory["cluster"] = _fake_cluster(dpm=dpm)
    result = vim_cluster_config.dpm_get(opts, "domain-c9")
    assert result["enabled"] is True
    assert result["default_behavior"] == "automated"
    assert result["host_power_action_rate"] == 4


def test_dpm_set(cluster_factory, opts):
    vim_cluster_config.dpm_set(opts, "domain-c9", enabled=True, default_behavior="automated")
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.dpmConfig.enabled is True
    assert spec.dpmConfig.defaultDpmBehavior == "automated"


# ---------- full HA/DRS knob surface (vmware_cluster_ha/drs parity) ----------


def test_drs_set_advanced_settings(cluster_factory, opts):
    vim_cluster_config.drs_set(opts, "domain-c9", advanced_settings={"Das.Foo": 1})
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.drsConfig.option[0].key == "Das.Foo"
    assert spec.drsConfig.option[0].value == 1


def test_drs_get_advanced_settings_readback(cluster_factory, opts):
    drs = vim.cluster.DrsConfigInfo()
    drs.enabled = True
    drs.vmotionRate = 3
    drs.option = [vim.option.OptionValue(key="Das.Foo", value=1)]
    cluster_factory["cluster"] = _fake_cluster(drs=drs)
    result = vim_cluster_config.drs_get(opts, "domain-c9")
    assert result["advanced_settings"] == {"Das.Foo": 1}


def test_ha_set_full_vm_settings(cluster_factory, opts):
    vim_cluster_config.ha_set(
        opts,
        "domain-c9",
        enabled=True,
        vm_component_protecting="enabled",
        vm_min_up_time=120,
        vm_max_failure_window=-1,
        vm_max_failures=3,
        vm_failure_interval=30,
        restart_priority_timeout=120,
        enable_apd_timeout_for_hosts=True,
        vm_reaction_on_apd_cleared="none",
        vm_storage_protection_for_apd="warning",
        vm_storage_protection_for_pdl="warning",
        vm_terminate_delay_for_apd_sec=180,
    )
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    das = spec.dasConfig
    assert das.vmComponentProtecting == "enabled"
    settings = das.defaultVmSettings
    assert settings.restartPriorityTimeout == 120
    tools = settings.vmToolsMonitoringSettings
    assert tools.minUpTime == 120
    assert tools.maxFailureWindow == -1
    assert tools.maxFailures == 3
    assert tools.failureInterval == 30
    vcp = settings.vmComponentProtectionSettings
    assert vcp.enableAPDTimeoutForHosts is True
    assert vcp.vmReactionOnAPDCleared == "none"
    assert vcp.vmStorageProtectionForAPD == "warning"
    assert vcp.vmStorageProtectionForPDL == "warning"
    assert vcp.vmTerminateDelayForAPDSec == 180


def test_ha_set_slot_based_admission_policy(cluster_factory, opts):
    vim_cluster_config.ha_set(
        opts,
        "domain-c9",
        admission_control_policy={
            "slot_based_admission_control": {
                "failover_level": 1,
                "resource_reduction_to_tolerate_percent": 20,
            }
        },
    )
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    policy = spec.dasConfig.admissionControlPolicy
    assert isinstance(policy, vim.cluster.FailoverLevelAdmissionControlPolicy)
    assert policy.failoverLevel == 1
    assert policy.resourceReductionToToleratePercent == 20


class _NamedHost(vim.HostSystem):
    _name = "esxi-01"

    @property
    def name(self):  # noqa: A003
        return _NamedHost._name


def test_ha_set_failover_host_admission_policy(cluster_factory, opts, monkeypatch):
    container = MagicMock()
    host = _NamedHost("host-1", None)
    container.view = [host]
    content = MagicMock()
    content.viewManager.CreateContainerView.return_value = container
    content.rootFolder = MagicMock()
    monkeypatch.setattr("saltext.vcf.utils.vim.content", lambda o, profile=None: content)
    vim_cluster_config.ha_set(
        opts,
        "domain-c9",
        admission_control_policy={
            "failover_host_admission_control": {
                "failover_level": 2,
                "failover_hosts": ["esxi-01"],
            }
        },
    )
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    policy = spec.dasConfig.admissionControlPolicy
    assert isinstance(policy, vim.cluster.FailoverHostAdmissionControlPolicy)
    assert policy.failoverLevel == 2
    assert policy.failoverHosts == [host]


def test_ha_set_reservation_based_admission_policy(cluster_factory, opts):
    vim_cluster_config.ha_set(
        opts,
        "domain-c9",
        admission_control_policy={
            "reservation_based_admission_control": {
                "failover_level": 3,
                "autocompute_percentages": False,
                "cpu_failover_resources_percent": 45,
                "memory_failover_resources_percent": 50,
            }
        },
    )
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    policy = spec.dasConfig.admissionControlPolicy
    assert isinstance(policy, vim.cluster.FailoverResourcesAdmissionControlPolicy)
    assert policy.autoComputePercentages is False
    assert policy.cpuFailoverResourcesPercent == 45
    assert policy.memoryFailoverResourcesPercent == 50


def test_ha_set_unknown_admission_policy_raises(cluster_factory, opts):
    import pytest

    with pytest.raises(ValueError):
        vim_cluster_config.ha_set(opts, "domain-c9", admission_control_policy={"bogus": {}})


def test_ha_set_preserves_existing_vm_settings(cluster_factory, opts):
    das = vim.cluster.DasConfigInfo()
    existing = vim.cluster.DasVmSettings()
    existing.restartPriority = "high"
    existing.isolationResponse = "powerOff"
    das.defaultVmSettings = existing
    cluster_factory["cluster"] = _fake_cluster(das=das)
    vim_cluster_config.ha_set(opts, "domain-c9", restart_priority="low")
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    settings = spec.dasConfig.defaultVmSettings
    assert settings.restartPriority == "low"
    # isolation_response was carried over, not clobbered to None
    assert settings.isolationResponse == "powerOff"


def test_ha_get_full_readback(cluster_factory, opts):
    das = vim.cluster.DasConfigInfo()
    das.enabled = True
    das.hostMonitoring = "enabled"
    das.vmMonitoring = "vmMonitoringOnly"
    das.admissionControlEnabled = True
    das.vmComponentProtecting = "enabled"
    settings = vim.cluster.DasVmSettings()
    settings.restartPriority = "medium"
    settings.isolationResponse = "powerOff"
    settings.restartPriorityTimeout = 120
    tools = vim.cluster.VmToolsMonitoringSettings()
    tools.minUpTime = 120
    tools.maxFailureWindow = -1
    tools.maxFailures = 3
    tools.failureInterval = 30
    settings.vmToolsMonitoringSettings = tools
    vcp = vim.cluster.VmComponentProtectionSettings()
    vcp.enableAPDTimeoutForHosts = True
    vcp.vmReactionOnAPDCleared = "none"
    vcp.vmStorageProtectionForAPD = "warning"
    vcp.vmStorageProtectionForPDL = "warning"
    vcp.vmTerminateDelayForAPDSec = 180
    settings.vmComponentProtectionSettings = vcp
    das.defaultVmSettings = settings
    cluster_factory["cluster"] = _fake_cluster(das=das)
    result = vim_cluster_config.ha_get(opts, "domain-c9")
    assert result["vm_component_protecting"] == "enabled"
    assert result["restart_priority_timeout"] == 120
    assert result["vm_min_up_time"] == 120
    assert result["vm_max_failure_window"] == -1
    assert result["vm_max_failures"] == 3
    assert result["vm_failure_interval"] == 30
    assert result["enable_apd_timeout_for_hosts"] is True
    assert result["vm_terminate_delay_for_apd_sec"] == 180


def test_get_config_aggregates(cluster_factory, opts):
    cl = _fake_cluster()
    cl.configurationEx.vsanConfigInfo = None
    cluster_factory["cluster"] = cl
    result = vim_cluster_config.get_config(opts, "domain-c9")
    assert result["enabled"] is False  # DRS disabled by default
    assert result["vsan_enabled"] is False
    assert "host_monitoring" in result
