"""Tests for clients.vim_dvs (VDS lifecycle via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_dvs


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
    dpc = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
    sec = vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy()
    sec.allowPromiscuous = vim.BoolPolicy(value=True)
    sec.macChanges = vim.BoolPolicy(value=True)
    sec.forgedTransmits = vim.BoolPolicy(value=True)
    dpc.securityPolicy = sec
    dvs.config.defaultPortConfig = dpc
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


# ---------- full configure surface (vmware_dvswitch.configure parity) ----------


def test_create_with_custom_uplink_prefix_and_discovery(factories, opts):
    from pyVmomi import vim as _vim

    vim_dvs.create(
        opts,
        "prod-dvs",
        "Datacenter",
        uplink_prefix="Uplink ",
        num_uplinks=2,
        discovery_protocol="cdp",
        discovery_operation="both",
        multicast_filtering_mode="basic",
        contact_name="admin",
        contact_description="noc",
    )
    spec = factories["dc"].networkFolder.CreateDVS_Task.call_args.kwargs["spec"]
    cfg = spec.configSpec
    assert cfg.uplinkPortPolicy.uplinkPortName == ["Uplink 1", "Uplink 2"]
    assert cfg.linkDiscoveryProtocolConfig.protocol == "cdp"
    assert cfg.linkDiscoveryProtocolConfig.operation == "both"
    assert cfg.multicastFilteringMode == "legacyFiltering"
    assert cfg.contact.name == "admin"


def test_create_with_security_policy(factories, opts):
    vim_dvs.create(
        opts,
        "prod-dvs",
        "Datacenter",
        network_promiscuous=False,
        network_mac_changes=False,
        network_forged_transmits=False,
    )
    spec = factories["dc"].networkFolder.CreateDVS_Task.call_args.kwargs["spec"]
    policy = spec.configSpec.defaultPortConfig.securityPolicy
    assert policy.allowPromiscuous.value is False
    assert policy.macChanges.value is False
    assert policy.forgedTransmits.value is False


def test_create_disabled_discovery_maps_to_none(factories, opts):
    vim_dvs.create(opts, "prod-dvs", "Datacenter", discovery_protocol="disabled")
    spec = factories["dc"].networkFolder.CreateDVS_Task.call_args.kwargs["spec"]
    ldp = spec.configSpec.linkDiscoveryProtocolConfig
    assert ldp.protocol == "cdp"
    assert ldp.operation == "none"


def test_reconfigure_updates_uplinks_and_security(factories, opts):
    vim_dvs.reconfigure(
        opts,
        "prod-dvs",
        num_uplinks=2,
        uplink_prefix="Uplink ",
        network_promiscuous=False,
    )
    spec = factories["dvs"].ReconfigureDvs_Task.call_args.kwargs["spec"]
    assert spec.uplinkPortPolicy.uplinkPortName == ["Uplink 1", "Uplink 2"]
    assert spec.defaultPortConfig.securityPolicy.allowPromiscuous.value is False


def test_reconfigure_version_second_task(factories, opts):
    vim_dvs.reconfigure(opts, "prod-dvs", version="9.0.0")
    calls = factories["dvs"].ReconfigureDvs_Task.call_args_list
    assert len(calls) == 2
    assert calls[1].kwargs["productSpec"].version == "9.0.0"


def test_reconfigure_health_checks(factories, opts):
    from pyVmomi import vim as _vim

    dvs = factories["dvs"]
    vlan_cfg = _vim.dvs.VmwareDistributedVirtualSwitch.VlanMtuHealthCheckConfig()
    vlan_cfg.enable = False
    vlan_cfg.interval = 1
    teaming_cfg = _vim.dvs.VmwareDistributedVirtualSwitch.TeamingHealthCheckConfig()
    teaming_cfg.enable = False
    teaming_cfg.interval = 1
    dvs.config.healthCheckConfig = [vlan_cfg, teaming_cfg]
    vim_dvs.reconfigure(
        opts,
        "prod-dvs",
        health_check_vlan_mtu=True,
        health_check_vlan_mtu_interval=5,
        health_check_teaming_failover=True,
        health_check_teaming_failover_interval=7,
    )
    dvs.UpdateHealthCheckConfig.assert_called_once()
    health = dvs.UpdateHealthCheckConfig.call_args.kwargs["healthCheckConfig"]
    by_type = {type(c).__name__.rsplit(".", 1)[-1]: c for c in health}
    assert by_type["VlanMtuHealthCheckConfig"].enable is True
    assert by_type["VlanMtuHealthCheckConfig"].interval == 5
    assert by_type["TeamingHealthCheckConfig"].enable is True
    assert by_type["TeamingHealthCheckConfig"].interval == 7
