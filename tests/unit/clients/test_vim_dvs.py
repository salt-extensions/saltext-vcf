"""Tests for clients.vim_dvs (VDS lifecycle via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_dvs


def _fake_dvs(
    name="prod-dvs", moid="dvs-1", uuid="uuid-1", num_ports=128, max_mtu=1500, version="9.0.0"
):
    dvs = MagicMock()
    dvs._moId = moid
    dvs.name = name
    dvs.uuid = uuid
    dvs.config.numPorts = num_ports
    dvs.config.maxMtu = max_mtu
    dvs.config.productInfo.version = version
    dvs.config.host = []
    dvs.config.uplinkPortPolicy.uplinkPortName = ["uplink1", "uplink2"]
    dvs.config.configVersion = "1"
    dvs.ReconfigureDvs_Task.return_value = MagicMock(_moId="task-1")
    dvs.Destroy_Task.return_value = MagicMock(_moId="task-2")
    return dvs


def _fake_datacenter():
    dc = MagicMock()
    dc.networkFolder.CreateDVS_Task.return_value = MagicMock(_moId="task-create")
    return dc


@pytest.fixture
def factories(monkeypatch):
    state = {
        "dvs": _fake_dvs(),
        "dc": _fake_datacenter(),
        "host": vim.HostSystem("host-1", None),
    }
    monkeypatch.setattr(vim_dvs, "_dvs", lambda o, n, profile=None: state["dvs"])
    monkeypatch.setattr(vim_dvs, "_datacenter", lambda o, n, profile=None: state["dc"])
    monkeypatch.setattr(vim_dvs, "_host", lambda o, n, profile=None: state["host"])
    return state


def test_get_returns_dict(factories, opts):
    result = vim_dvs.get(opts, "prod-dvs")
    assert result["name"] == "prod-dvs"
    assert result["uuid"] == "uuid-1"
    assert result["version"] == "9.0.0"
    assert result["num_ports"] == 128
    assert result["uplink_port_names"] == ["uplink1", "uplink2"]


def test_get_or_none_missing(monkeypatch, opts):
    def _raise(o, n, profile=None):
        raise LookupError("nope")

    monkeypatch.setattr(vim_dvs, "_dvs", _raise)
    assert vim_dvs.get_or_none(opts, "nope") is None


def test_create_with_defaults(factories, opts):
    vim_dvs.create(opts, "prod-dvs", "Datacenter")
    call = factories["dc"].networkFolder.CreateDVS_Task.call_args
    spec = call.kwargs["spec"]
    assert spec.configSpec.name == "prod-dvs"
    assert spec.configSpec.maxMtu == 1500
    # Default 4 uplinks
    uplink_names = spec.configSpec.uplinkPortPolicy.uplinkPortName
    assert uplink_names == ["uplink1", "uplink2", "uplink3", "uplink4"]
    # Version not specified
    assert spec.productInfo is None


def test_create_with_version(factories, opts):
    vim_dvs.create(opts, "prod-dvs", "Datacenter", version="9.0.0", num_uplinks=2)
    spec = factories["dc"].networkFolder.CreateDVS_Task.call_args.kwargs["spec"]
    assert spec.productInfo.version == "9.0.0"
    assert spec.configSpec.uplinkPortPolicy.uplinkPortName == ["uplink1", "uplink2"]


def test_reconfigure_max_mtu(factories, opts):
    vim_dvs.reconfigure(opts, "prod-dvs", max_mtu=9000)
    spec = factories["dvs"].ReconfigureDvs_Task.call_args.kwargs["spec"]
    assert spec.maxMtu == 9000
    assert spec.configVersion == "1"


def test_reconfigure_only_passes_non_none(factories, opts):
    vim_dvs.reconfigure(opts, "prod-dvs", description="new desc")
    spec = factories["dvs"].ReconfigureDvs_Task.call_args.kwargs["spec"]
    assert spec.description == "new desc"
    assert spec.maxMtu is None


def test_delete(factories, opts):
    vim_dvs.delete(opts, "prod-dvs")
    factories["dvs"].Destroy_Task.assert_called_once()


def test_add_host_includes_pnic_backing(factories, opts):
    vim_dvs.add_host(opts, "prod-dvs", "esxi-01", pnic_devices=["vmnic0", "vmnic1"])
    spec = factories["dvs"].ReconfigureDvs_Task.call_args.kwargs["spec"]
    assert len(spec.host) == 1
    member_cfg = spec.host[0]
    assert member_cfg.operation == "add"
    assert member_cfg.host is factories["host"]
    assert len(member_cfg.backing.pnicSpec) == 2
    assert {p.pnicDevice for p in member_cfg.backing.pnicSpec} == {"vmnic0", "vmnic1"}


def test_remove_host(factories, opts):
    vim_dvs.remove_host(opts, "prod-dvs", "esxi-01")
    spec = factories["dvs"].ReconfigureDvs_Task.call_args.kwargs["spec"]
    assert spec.host[0].operation == "remove"
    assert spec.host[0].host is factories["host"]
