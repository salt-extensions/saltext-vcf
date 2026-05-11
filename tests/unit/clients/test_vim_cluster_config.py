"""Tests for clients.vim_cluster_config (DRS / HA / EVC / DPM via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_cluster_config


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
