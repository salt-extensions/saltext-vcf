"""Tests for clients.vim_host_network (standard switch / portgroup / vmkernel via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_host_network


def _vswitch(name="vSwitch0", num_ports=128, num_avail=120, mtu=1500, pnics=None, portgroups=()):
    vs = MagicMock()
    vs.name = name
    vs.key = f"key-{name}"
    vs.numPorts = num_ports
    vs.numPortsAvailable = num_avail
    vs.mtu = mtu
    vs.portgroup = list(portgroups)
    if pnics:
        bridge = vim.host.VirtualSwitch.BondBridge()
        bridge.nicDevice = list(pnics)
        vs.spec.bridge = bridge
    else:
        vs.spec.bridge = None
    return vs


def _portgroup(name, vlan=0, vswitch="vSwitch0", port_count=2):
    pg = MagicMock()
    pg.spec.name = name
    pg.spec.vlanId = vlan
    pg.spec.vswitchName = vswitch
    pg.port = [MagicMock() for _ in range(port_count)]
    return pg


def _vnic(
    device="vmk0",
    portgroup="Management",
    mac="00:50:56:00:00:01",
    dhcp=False,
    ip="10.0.0.5",
    mask="255.255.255.0",
    mtu=1500,
):
    vnic = MagicMock()
    vnic.device = device
    vnic.portgroup = portgroup
    vnic.port = f"port-{device}"
    vnic.spec.mac = mac
    vnic.spec.mtu = mtu
    ip_cfg = MagicMock()
    ip_cfg.dhcp = dhcp
    ip_cfg.ipAddress = ip
    ip_cfg.subnetMask = mask
    vnic.spec.ip = ip_cfg
    return vnic


def _pnic(device="vmnic0", driver="ixgbe", mac="aa:bb:cc:dd:ee:ff", duplex="full", speed_mb=10000):
    p = MagicMock()
    p.device = device
    p.driver = driver
    p.mac = mac
    p.wakeOnLanSupported = True
    p.linkSpeed.duplex = duplex
    p.linkSpeed.speedMb = speed_mb
    return p


def _fake_host(vswitches=None, portgroups=None, vnics=None, pnics=None):
    h = MagicMock()
    h.config.network.vswitch = vswitches or []
    h.config.network.portgroup = portgroups or []
    h.config.network.vnic = vnics or []
    h.config.network.pnic = pnics or []
    h.configManager.networkSystem = MagicMock()
    h.configManager.networkSystem.AddVirtualNic.return_value = "vmk1"
    return h


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(vim_host_network, "_host", lambda o, h, profile=None: holder["host"])
    return holder


# ---------- vSwitches ----------


def test_vswitch_list_returns_records(host_factory, opts):
    host_factory["host"] = _fake_host(
        vswitches=[
            _vswitch("vSwitch0", pnics=["vmnic0"]),
            _vswitch("vSwitch1", mtu=9000),
        ]
    )
    result = vim_host_network.vswitch_list(opts, "esxi-01")
    by_name = {v["name"]: v for v in result}
    assert by_name["vSwitch0"]["pnic_devices"] == ["vmnic0"]
    assert by_name["vSwitch1"]["mtu"] == 9000


def test_vswitch_get_or_none_missing(host_factory, opts):
    assert vim_host_network.vswitch_get_or_none(opts, "esxi-01", "vSwitch99") is None


def test_vswitch_add_without_pnics(host_factory, opts):
    vim_host_network.vswitch_add(opts, "esxi-01", "vSwitch1")
    call = host_factory["host"].configManager.networkSystem.AddVirtualSwitch.call_args
    assert call.kwargs["vswitchName"] == "vSwitch1"
    spec = call.kwargs["spec"]
    assert spec.numPorts == 128
    assert spec.mtu == 1500
    assert spec.bridge is None


def test_vswitch_add_with_pnics(host_factory, opts):
    vim_host_network.vswitch_add(opts, "esxi-01", "vSwitch1", pnic_devices=["vmnic1", "vmnic2"])
    spec = host_factory["host"].configManager.networkSystem.AddVirtualSwitch.call_args.kwargs[
        "spec"
    ]
    assert isinstance(spec.bridge, vim.host.VirtualSwitch.BondBridge)
    assert spec.bridge.nicDevice == ["vmnic1", "vmnic2"]


def test_vswitch_update_merges_existing(host_factory, opts):
    host_factory["host"] = _fake_host(vswitches=[_vswitch("vSwitch0", mtu=1500, pnics=["vmnic0"])])
    vim_host_network.vswitch_update(opts, "esxi-01", "vSwitch0", mtu=9000)
    spec = host_factory["host"].configManager.networkSystem.UpdateVirtualSwitch.call_args.kwargs[
        "spec"
    ]
    # MTU updated, pnics preserved from existing config
    assert spec.mtu == 9000
    assert spec.bridge.nicDevice == ["vmnic0"]


def test_vswitch_remove(host_factory, opts):
    vim_host_network.vswitch_remove(opts, "esxi-01", "vSwitch1")
    host_factory["host"].configManager.networkSystem.RemoveVirtualSwitch.assert_called_once_with(
        vswitchName="vSwitch1"
    )


# ---------- Port groups ----------


def test_portgroup_list(host_factory, opts):
    host_factory["host"] = _fake_host(
        portgroups=[
            _portgroup("Management", vlan=10),
            _portgroup("vMotion", vlan=20),
        ]
    )
    result = vim_host_network.portgroup_list(opts, "esxi-01")
    by_name = {pg["name"]: pg for pg in result}
    assert by_name["Management"]["vlan_id"] == 10
    assert by_name["vMotion"]["vswitch"] == "vSwitch0"


def test_portgroup_add(host_factory, opts):
    vim_host_network.portgroup_add(opts, "esxi-01", "Mgmt", "vSwitch0", vlan_id=10)
    call = host_factory["host"].configManager.networkSystem.AddPortGroup.call_args
    spec = call.kwargs["portgrp"]
    assert spec.name == "Mgmt"
    assert spec.vlanId == 10
    assert spec.vswitchName == "vSwitch0"


def test_portgroup_update_preserves_vswitch(host_factory, opts):
    host_factory["host"] = _fake_host(portgroups=[_portgroup("Mgmt", vlan=10, vswitch="vSwitch0")])
    vim_host_network.portgroup_update(opts, "esxi-01", "Mgmt", vlan_id=20)
    spec = host_factory["host"].configManager.networkSystem.UpdatePortGroup.call_args.kwargs[
        "portgrp"
    ]
    assert spec.vlanId == 20
    assert spec.vswitchName == "vSwitch0"


def test_portgroup_add_with_security_policy(host_factory, opts):
    """Nested-VM labs need promiscuous + macChanges + forgedTransmits Accept."""
    vim_host_network.portgroup_add(
        opts,
        "esxi-01",
        "nested",
        "vSwitch1",
        vlan_id=0,
        promiscuous=True,
        mac_changes=True,
        forged_transmits=True,
    )
    spec = host_factory["host"].configManager.networkSystem.AddPortGroup.call_args.kwargs["portgrp"]
    assert spec.policy.security.allowPromiscuous is True
    assert spec.policy.security.macChanges is True
    assert spec.policy.security.forgedTransmits is True


def test_portgroup_add_default_inherits_vswitch_policy(host_factory, opts):
    """No security kwargs → empty NetworkPolicy so the port group inherits."""
    vim_host_network.portgroup_add(opts, "esxi-01", "Mgmt", "vSwitch0")
    spec = host_factory["host"].configManager.networkSystem.AddPortGroup.call_args.kwargs["portgrp"]
    assert spec.policy.security is None


def test_portgroup_update_with_security_policy(host_factory, opts):
    host_factory["host"] = _fake_host(portgroups=[_portgroup("Mgmt", vlan=10, vswitch="vSwitch0")])
    vim_host_network.portgroup_update(
        opts,
        "esxi-01",
        "Mgmt",
        promiscuous=False,
        mac_changes=True,
        forged_transmits=False,
    )
    spec = host_factory["host"].configManager.networkSystem.UpdatePortGroup.call_args.kwargs[
        "portgrp"
    ]
    assert spec.policy.security.allowPromiscuous is False
    assert spec.policy.security.macChanges is True
    assert spec.policy.security.forgedTransmits is False


def test_portgroup_list_exposes_security_in_dict(host_factory, opts):
    pg = _portgroup("Mgmt", vlan=10)
    sec = MagicMock()
    sec.allowPromiscuous = True
    sec.macChanges = False
    sec.forgedTransmits = True
    pg.spec.policy.security = sec
    host_factory["host"] = _fake_host(portgroups=[pg])
    result = vim_host_network.portgroup_list(opts, "esxi-01")
    assert result[0]["security"] == {
        "promiscuous": True,
        "mac_changes": False,
        "forged_transmits": True,
    }


def test_portgroup_remove(host_factory, opts):
    vim_host_network.portgroup_remove(opts, "esxi-01", "Mgmt")
    host_factory["host"].configManager.networkSystem.RemovePortGroup.assert_called_once_with(
        pgName="Mgmt"
    )


# ---------- VMkernel ----------


def test_vmkernel_list(host_factory, opts):
    host_factory["host"] = _fake_host(
        vnics=[_vnic("vmk0", "Management"), _vnic("vmk1", "vMotion", ip="10.1.1.5")]
    )
    result = vim_host_network.vmkernel_list(opts, "esxi-01")
    by_dev = {v["device"]: v for v in result}
    assert by_dev["vmk0"]["portgroup"] == "Management"
    assert by_dev["vmk1"]["ip_address"] == "10.1.1.5"


def test_vmkernel_add_static_ip(host_factory, opts):
    device = vim_host_network.vmkernel_add(
        opts,
        "esxi-01",
        "vMotion",
        ip_address="10.0.0.5",
        subnet_mask="255.255.255.0",
        mtu=9000,
    )
    assert device == "vmk1"
    call = host_factory["host"].configManager.networkSystem.AddVirtualNic.call_args
    assert call.kwargs["portgroup"] == "vMotion"
    spec = call.kwargs["nic"]
    assert spec.ip.dhcp is False
    assert spec.ip.ipAddress == "10.0.0.5"
    assert spec.mtu == 9000


def test_vmkernel_add_dhcp(host_factory, opts):
    vim_host_network.vmkernel_add(opts, "esxi-01", "Management", dhcp=True)
    spec = host_factory["host"].configManager.networkSystem.AddVirtualNic.call_args.kwargs["nic"]
    assert spec.ip.dhcp is True


def test_vmkernel_add_requires_ip_or_dhcp(host_factory, opts):
    with pytest.raises(ValueError, match="dhcp.*ip_address"):
        vim_host_network.vmkernel_add(opts, "esxi-01", "Mgmt")


def test_vmkernel_update_preserves_existing(host_factory, opts):
    host_factory["host"] = _fake_host(
        vnics=[_vnic("vmk1", "vMotion", ip="10.0.0.5", mask="255.255.255.0", mtu=1500)]
    )
    vim_host_network.vmkernel_update(opts, "esxi-01", "vmk1", mtu=9000)
    spec = host_factory["host"].configManager.networkSystem.UpdateVirtualNic.call_args.kwargs["nic"]
    assert spec.mtu == 9000
    assert spec.ip.ipAddress == "10.0.0.5"  # preserved


def test_vmkernel_remove(host_factory, opts):
    vim_host_network.vmkernel_remove(opts, "esxi-01", "vmk1")
    host_factory["host"].configManager.networkSystem.RemoveVirtualNic.assert_called_once_with(
        device="vmk1"
    )


def test_physical_nic_list(host_factory, opts):
    host_factory["host"] = _fake_host(pnics=[_pnic("vmnic0", driver="ixgbe", speed_mb=10000)])
    result = vim_host_network.physical_nic_list(opts, "esxi-01")
    assert len(result) == 1
    assert result[0]["device"] == "vmnic0"
    assert result[0]["speed_mb"] == 10000


def test_vmkernel_set_traffic_types(host_factory, opts):
    host = host_factory["host"]
    vnic_mgr = MagicMock()
    vnic_mgr.info.netConfig = []
    host.configManager.virtualNicManager = vnic_mgr
    vim_host_network.vmkernel_set_traffic_types(
        opts, "esxi-01", "vmk1", ["vmotion", "provisioning"]
    )
    calls = [c.kwargs for c in vnic_mgr.SelectVnicForNicType.call_args_list]
    nic_types = {c["nicType"] for c in calls}
    assert nic_types == {"vmotion", "provisioning"}
    assert all(c["device"] == "vmk1" for c in calls)
