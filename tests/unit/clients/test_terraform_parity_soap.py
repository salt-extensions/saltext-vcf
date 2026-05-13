"""SOAP unit tests for the Terraform-parity batch.

Cluster overrides, datastore cluster, and host datastore. Each uses
MagicMock-based pyVmomi stand-ins; we verify the right ConfigSpec /
RelocateSpec / DatastoreSystem call shape goes out.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_cluster_overrides
from saltext.vmware.clients import vim_datastore_cluster
from saltext.vmware.clients import vim_host_datastore

# ---------------------------------------------------------------------------
# Cluster overrides
# ---------------------------------------------------------------------------


def _fake_cluster(drs_vm=None, das_vm=None, dpm_host=None):
    cl = MagicMock()
    cl._moId = "domain-c1"
    cl.name = "test-cluster"
    cfg = cl.configurationEx
    cfg.drsVmConfig = drs_vm or []
    cfg.dasVmConfig = das_vm or []
    cfg.dpmHostConfig = dpm_host or []
    cl.ReconfigureComputeResource_Task.return_value = MagicMock(_moId="task-x")
    return cl


@pytest.fixture
def cluster_factory(monkeypatch):
    holder = {"cl": _fake_cluster()}

    def patcher(opts, name, profile=None):
        return holder["cl"]

    monkeypatch.setattr(vim_cluster_overrides, "_cluster", patcher)
    return holder


def test_drs_vm_set_add(cluster_factory, opts):
    out = vim_cluster_overrides.drs_vm_set(opts, "test-cluster", "vm-1", "manual")
    assert out == "task-x"
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    drs = spec.drsVmConfigSpec[0]
    assert drs.operation == "add"
    assert drs.info.behavior == vim.cluster.DrsConfigInfo.DrsBehavior.manual
    assert drs.info.key._moId == "vm-1"  # noqa: SLF001


def test_drs_vm_set_edit_when_exists(cluster_factory, opts):
    existing = MagicMock()
    existing.key._moId = "vm-1"  # noqa: SLF001
    cluster_factory["cl"] = _fake_cluster(drs_vm=[existing])
    vim_cluster_overrides.drs_vm_set(opts, "test-cluster", "vm-1", "fullyAutomated")
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.drsVmConfigSpec[0].operation == "edit"


def test_drs_vm_remove(cluster_factory, opts):
    vim_cluster_overrides.drs_vm_remove(opts, "test-cluster", "vm-1")
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.drsVmConfigSpec[0].operation == "remove"


def test_ha_vm_set(cluster_factory, opts):
    vim_cluster_overrides.ha_vm_set(
        opts, "test-cluster", "vm-1", restart_priority="high", isolation_response="powerOff"
    )
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    das = spec.dasVmConfigSpec[0]
    assert das.info.dasSettings.restartPriority == "high"
    assert das.info.dasSettings.isolationResponse == "powerOff"


def test_ha_vm_remove(cluster_factory, opts):
    vim_cluster_overrides.ha_vm_remove(opts, "test-cluster", "vm-1")
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.dasVmConfigSpec[0].operation == "remove"


def test_dpm_host_set(cluster_factory, opts):
    vim_cluster_overrides.dpm_host_set(opts, "test-cluster", "host-1", "manual")
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    dpm = spec.dpmHostConfigSpec[0]
    assert dpm.info.behavior == "manual"
    assert dpm.info.key._moId == "host-1"  # noqa: SLF001


def test_dpm_host_remove(cluster_factory, opts):
    vim_cluster_overrides.dpm_host_remove(opts, "test-cluster", "host-1")
    spec = cluster_factory["cl"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.dpmHostConfigSpec[0].operation == "remove"


def test_drs_vm_list_shape(cluster_factory, opts):
    entry = MagicMock()
    entry.key._moId = "vm-1"  # noqa: SLF001
    entry.enabled = True
    entry.behavior = "manual"
    cluster_factory["cl"] = _fake_cluster(drs_vm=[entry])
    rows = vim_cluster_overrides.drs_vm_list(opts, "test-cluster")
    assert rows == [{"vm_moid": "vm-1", "enabled": True, "behavior": "manual"}]


def test_module_wrappers_delegate(cluster_factory, opts, monkeypatch):
    from saltext.vmware.modules import vmware_vim_cluster_overrides as m

    monkeypatch.setattr(m, "__opts__", opts, raising=False)
    assert m.drs_vm_set("test-cluster", "vm-1", "manual") == "task-x"
    assert m.dpm_host_set("test-cluster", "host-1", "manual") == "task-x"


# ---------------------------------------------------------------------------
# Host datastore
# ---------------------------------------------------------------------------


def _fake_host(datastores=None):
    h = MagicMock()
    h._moId = "host-7"
    h.name = "esxi-1"
    h.datastore = datastores or []
    h.configManager.datastoreSystem.QueryAvailableDisksForVmfs.return_value = []
    return h


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"h": _fake_host()}

    def patcher(opts, name, profile=None):
        return holder["h"]

    monkeypatch.setattr(vim_host_datastore, "_resolve_host", patcher)
    return holder


def test_host_datastore_list(host_factory, opts):
    ds1 = MagicMock()
    ds1._moId = "ds-1"  # noqa: SLF001
    ds1.summary.name = "shared-iso"
    ds1.summary.type = "NFS"
    ds1.summary.url = "nfs://10.0.0.5/exports/iso"
    ds1.summary.capacity = 1000
    ds1.summary.freeSpace = 500
    ds1.summary.accessible = True
    host_factory["h"] = _fake_host(datastores=[ds1])
    out = vim_host_datastore.list_(opts, "esxi-1")
    assert out[0]["name"] == "shared-iso"
    assert out[0]["type"] == "NFS"


def test_host_datastore_mount_nfs(host_factory, opts):
    new_ds = MagicMock()
    new_ds._moId = "ds-new"  # noqa: SLF001
    host_factory["h"].configManager.datastoreSystem.CreateNasDatastore.return_value = new_ds
    out = vim_host_datastore.mount_nfs(opts, "esxi-1", "iso", "10.0.0.5", "/exports/iso")
    assert out == "ds-new"
    call = host_factory["h"].configManager.datastoreSystem.CreateNasDatastore.call_args
    spec = call.kwargs["spec"]
    assert spec.remoteHost == "10.0.0.5"
    assert spec.remotePath == "/exports/iso"
    assert spec.localPath == "iso"


def test_host_datastore_remove(host_factory, opts):
    ds1 = MagicMock()
    ds1._moId = "ds-1"  # noqa: SLF001
    ds1.name = "shared-iso"
    host_factory["h"] = _fake_host(datastores=[ds1])
    assert vim_host_datastore.remove(opts, "esxi-1", "shared-iso") is True
    host_factory["h"].configManager.datastoreSystem.RemoveDatastore.assert_called_once_with(
        datastore=ds1
    )


def test_host_datastore_remove_missing_raises(host_factory, opts):
    with pytest.raises(LookupError):
        vim_host_datastore.remove(opts, "esxi-1", "nope")


def test_host_datastore_rescan(host_factory, opts):
    assert vim_host_datastore.rescan_storage(opts, "esxi-1") is True
    host_factory["h"].configManager.storageSystem.RescanAllHba.assert_called_once()


# ---------------------------------------------------------------------------
# Datastore cluster (StoragePod)
# ---------------------------------------------------------------------------


def _fake_pod():
    pod = MagicMock()
    pod._moId = "group-p1"
    pod.name = "ds-cluster"
    pod.childEntity = []
    pod.Destroy_Task.return_value = MagicMock(_moId="task-pod-del")
    return pod


@pytest.fixture
def pod_factory(monkeypatch):
    holder = {"pod": _fake_pod()}
    monkeypatch.setattr(
        vim_datastore_cluster, "_resolve_pod", lambda opts, name, profile=None: holder["pod"]
    )
    return holder


def test_datastore_cluster_get_shape(pod_factory, opts):
    ds_member = MagicMock()
    ds_member.name = "ds-shared"
    pod_factory["pod"].childEntity = [ds_member]
    out = vim_datastore_cluster.get(opts, "ds-cluster")
    assert out["name"] == "ds-cluster"
    assert out["datastores"] == ["ds-shared"]


def test_datastore_cluster_delete(pod_factory, opts):
    assert vim_datastore_cluster.delete(opts, "ds-cluster") == "task-pod-del"


def test_datastore_cluster_sdrs_get(pod_factory, opts):
    sdrs = pod_factory["pod"].podStorageDrsEntry.storageDrsConfig.podConfig
    sdrs.enabled = True
    sdrs.defaultVmBehavior = "automated"
    sdrs.ioLoadBalanceEnabled = True
    sdrs.spaceLoadBalanceConfig.spaceUtilizationThreshold = 80
    out = vim_datastore_cluster.sdrs_get(opts, "ds-cluster")
    assert out["enabled"] is True
    assert out["automation_level"] == "automated"
    assert out["space_utilization_threshold"] == 80
