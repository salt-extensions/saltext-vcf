"""Tests for clients.vim_host (lifecycle, power, capabilities, info aggregator)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_host


def _fake_host(name="esxi-01", conn="connected", standby="none"):
    h = MagicMock()
    h.name = name
    h.summary.runtime.connectionState = conn
    h.runtime.standbyMode = standby
    h.ReconnectHost_Task.return_value = MagicMock(_moId="task-r1")
    h.DisconnectHost_Task.return_value = MagicMock(_moId="task-d1")
    h.Destroy_Task.return_value = MagicMock(_moId="task-x1")
    h.RebootHost_Task.return_value = MagicMock(_moId="task-b1")
    h.ShutdownHost_Task.return_value = MagicMock(_moId="task-s1")
    h.PowerDownHostToStandBy_Task.return_value = MagicMock(_moId="task-sb1")
    h.PowerUpHostFromStandBy_Task.return_value = MagicMock(_moId="task-up1")
    # capability introspection
    cap = MagicMock()
    cap.vsanAPITypes = 3
    cap.snapshotSupported = True
    h.capability = cap
    return h


@pytest.fixture
def factory(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(vim_host, "_resolve", lambda o, n, profile=None: holder["host"])
    return holder


def _content_with_cluster(cluster_name="cl-1", cluster_moid="domain-c9"):
    content = MagicMock()
    cluster = MagicMock()
    cluster.name = cluster_name
    cluster._moId = cluster_moid  # noqa: SLF001
    cluster.MoveInto_Task.return_value = MagicMock(_moId="task-move1")
    cluster.AddHost_Task.return_value = MagicMock(_moId="task-add1")
    container = MagicMock()
    container.view = [cluster]
    content.viewManager.CreateContainerView.return_value = container
    content.rootFolder = MagicMock()
    return content, cluster


def test_reconnect_idempotent_when_connected(factory, opts):
    assert vim_host.reconnect(opts, "esxi-01") == "connected"
    factory["host"].ReconnectHost_Task.assert_not_called()


def test_disconnect_disconnected_noop(factory, opts):
    factory["host"].summary.runtime.connectionState = "disconnected"
    with patch.object(soap_mod(), "wait_for_task", lambda t, **kw: None):
        assert vim_host.disconnect(opts, "esxi-01") == "disconnected"
    factory["host"].DisconnectHost_Task.assert_not_called()


def soap_mod():
    from saltext.vcf.utils import vim as soap

    return soap


def test_destroy_waits_for_task(factory, opts, monkeypatch):
    monkeypatch.setattr("saltext.vcf.utils.vim.wait_for_task", lambda t, **kw: None)
    assert vim_host.destroy(opts, "esxi-01") == "task-x1"


def test_move_same_dc(factory, opts, monkeypatch):
    content, cluster = _content_with_cluster()
    h = factory["host"]
    # host parent chain: ComputeResource -> Datacenter
    dc = MagicMock(spec=vim.Datacenter)
    dc._moId = "dc-1"  # noqa: SLF001
    cr = MagicMock(spec=vim.ComputeResource)
    cr.parent = dc
    h.parent = cr
    cluster_dc = MagicMock(spec=vim.Datacenter)
    cluster_dc._moId = "dc-1"  # noqa: SLF001
    cluster.parent.parent = cluster_dc
    monkeypatch.setattr("saltext.vcf.utils.vim.content", lambda o, profile=None: content)
    monkeypatch.setattr("saltext.vcf.utils.vim.wait_for_task", lambda t, **kw: None)
    ret = vim_host.move(opts, "esxi-01", "cl-1")
    assert "moved esxi-01" in ret
    cluster.MoveInto_Task.assert_called_once()


def test_move_cross_dc_raises(factory, opts, monkeypatch):
    content, cluster = _content_with_cluster()
    h = factory["host"]
    dc1 = MagicMock(spec=vim.Datacenter)
    dc1._moId = "dc-1"  # noqa: SLF001
    cr = MagicMock(spec=vim.ComputeResource)
    cr.parent = dc1
    h.parent = cr
    dc2 = MagicMock(spec=vim.Datacenter)
    dc2._moId = "dc-2"  # noqa: SLF001
    cluster.parent.parent = dc2
    monkeypatch.setattr("saltext.vcf.utils.vim.content", lambda o, profile=None: content)
    with pytest.raises(RuntimeError):
        vim_host.move(opts, "esxi-01", "cl-1")


def test_power_state_reboot(factory, opts):
    out = vim_host.power_state(opts, "esxi-01", "reboot")
    assert out == {"task": "task-b1"}
    factory["host"].RebootHost_Task.assert_called_once_with(True)


def test_power_state_standby_idempotent(factory, opts):
    factory["host"].runtime.standbyMode = "entered"
    out = vim_host.power_state(opts, "esxi-01", "standby")
    assert out == {"already": "standby"}


def test_power_state_standby_transitions(factory, opts):
    factory["host"].runtime.standbyMode = "none"
    out = vim_host.power_state(opts, "esxi-01", "standby", timeout=120, force=False)
    assert out["task"] == "task-sb1"
    args = factory["host"].PowerDownHostToStandBy_Task.call_args.args
    assert args[0] == 120  # timeoutSec
    assert args[1] is False  # evacuatePoweredOffVms


def test_power_state_invalid(factory, opts):
    with pytest.raises(ValueError):
        vim_host.power_state(opts, "esxi-01", "hibernate")


def test_capabilities_snake_case(factory, opts):
    out = vim_host.capabilities(opts, "esxi-01")
    assert out["vsan_a_p_i_types"] == 3 or "vsan_a_p_i_types" in out
    assert "array" not in out


def test_info_aggregator(factory, opts):
    h = factory["host"]
    h.summary.hardware.cpuModel = "EPYC"
    h.summary.hardware.numCpuCores = 32
    h.summary.quickStats.overallMemoryUsage = 1000
    h.config.product.name = "VMware ESXi"
    h.hardware.systemInfo.vendor = "Dell"
    h.hardware.systemInfo.model = "R750"
    h.hardware.biosInfo.releaseDate = "2026-01-01"
    h.hardware.biosInfo.biosVersion = "2.1"
    h.summary.quickStats.uptime = 12345
    h.runtime.inMaintenanceMode = False
    h.hardware.systemInfo.uuid = "sys-uuid"
    h.hardware.systemInfo.otherIdentifyingInfo = []
    ds = MagicMock()
    ds.name = "ds1"
    ds.summary.capacity = 1
    ds.summary.freeSpace = 2
    h.datastore = [ds]
    nic = MagicMock()
    nic.device = "vmk0"
    nic.spec.ip.ipAddress = "10.0.0.5"
    nic.spec.ip.subnetMask = "255.255.255.0"
    nic.spec.mac = "00:50:56"
    nic.spec.mtu = 1500
    h.config.network.vnic = [nic]
    out = vim_host.info(opts, "esxi-01")
    assert out["cpu_model"] == "EPYC"
    assert out["datastores"]["ds1"]["capacity"] == 1
    assert out["nics"]["vmk0"]["ip_address"] == "10.0.0.5"
    assert out["in_maintenance_mode"] is False


def test_info_key_traversal(factory, opts):
    h = factory["host"]
    h.summary.quickStats.uptime = 99
    h.config.product.version = "9.0.0"
    h.hardware.systemInfo.otherIdentifyingInfo = []
    # flat keys traverse as single segments
    assert vim_host.info(opts, "esxi-01", key="product_version") == "9.0.0"
    # nested dicts (vsan) traverse with the delimiter
    h.configManager.vsanSystem.QueryHostStatus.return_value.health = "good"
    assert vim_host.info(opts, "esxi-01", key="vsan:health") == "good"
    assert vim_host.info(opts, "esxi-01", key="missing:thing", default="x") == "x"
