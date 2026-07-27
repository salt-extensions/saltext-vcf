"""Tests for clients.vim_dvs_portgroup (DPG lifecycle via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_dvs_portgroup


def _vlan_pg(
    name="prod-web", key="dvportgroup-25", num_ports=8, vlan_id=100, pg_type="earlyBinding"
):
    pg = MagicMock()
    pg._moId = key
    pg.key = key
    pg.name = name
    pg.config.numPorts = num_ports
    pg.config.type = pg_type
    pg.config.portBinding = pg_type
    pg.config.configVersion = "1"
    vlan = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec(vlanId=vlan_id)
    pg.config.defaultPortConfig.vlan = vlan
    pg.ReconfigureDVPortgroup_Task.return_value = MagicMock(_moId="task-rpg")
    pg.Destroy_Task.return_value = MagicMock(_moId="task-del")
    return pg


def _trunk_pg(name="trunk", ranges=((100, 200),)):
    pg = MagicMock()
    pg._moId = "dvportgroup-trunk"
    pg.key = "dvportgroup-trunk"
    pg.name = name
    pg.config.numPorts = 8
    pg.config.type = "earlyBinding"
    pg.config.portBinding = "earlyBinding"
    pg.config.configVersion = "1"
    trunk = vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec(
        vlanId=[vim.NumericRange(start=int(s), end=int(e)) for s, e in ranges]
    )
    pg.config.defaultPortConfig.vlan = trunk
    return pg


def _fake_dvs(portgroups=None):
    dvs = MagicMock()
    dvs._moId = "dvs-1"
    dvs.name = "prod-dvs"
    dvs.portgroup = portgroups or []
    dvs.AddDVPortgroup_Task.return_value = MagicMock(_moId="task-add")
    return dvs


@pytest.fixture
def dvs_factory(monkeypatch):
    holder = {"dvs": _fake_dvs()}
    monkeypatch.setattr(vim_dvs_portgroup, "_dvs", lambda o, n, profile=None: holder["dvs"])
    return holder


def test_list_vlan_pg(dvs_factory, opts):
    pg = _vlan_pg(vlan_id=100)
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    result = vim_dvs_portgroup.list_(opts, "prod-dvs")
    assert len(result) == 1
    assert result[0]["name"] == "prod-web"
    assert result[0]["vlan"] == {"kind": "vlan", "vlan_id": 100}


def test_list_trunk_pg(dvs_factory, opts):
    pg = _trunk_pg(ranges=((100, 200), (300, 400)))
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    result = vim_dvs_portgroup.list_(opts, "prod-dvs")
    assert result[0]["vlan"]["kind"] == "trunk"
    assert result[0]["vlan"]["ranges"] == [
        {"start": 100, "end": 200},
        {"start": 300, "end": 400},
    ]


def test_get_or_none_missing(dvs_factory, opts):
    dvs_factory["dvs"] = _fake_dvs(portgroups=[])
    assert vim_dvs_portgroup.get_or_none(opts, "prod-dvs", "nope") is None


def test_create_vlan_passes_spec(dvs_factory, opts):
    vim_dvs_portgroup.create_vlan(opts, "prod-dvs", "prod-web", vlan_id=100, num_ports=16)
    call = dvs_factory["dvs"].AddDVPortgroup_Task.call_args
    specs = call.kwargs["spec"]
    assert len(specs) == 1
    spec = specs[0]
    assert spec.name == "prod-web"
    assert spec.numPorts == 16
    assert spec.type == "earlyBinding"
    assert spec.defaultPortConfig.vlan.vlanId == 100


def test_create_vlan_promiscuous(dvs_factory, opts):
    vim_dvs_portgroup.create_vlan(opts, "prod-dvs", "promisc", vlan_id=0, promiscuous=True)
    spec = dvs_factory["dvs"].AddDVPortgroup_Task.call_args.kwargs["spec"][0]
    assert spec.defaultPortConfig.securityPolicy.allowPromiscuous.value is True


def test_create_trunk_passes_ranges(dvs_factory, opts):
    vim_dvs_portgroup.create_trunk(
        opts, "prod-dvs", "trunk-1", vlan_ranges=[(100, 200), (300, 400)]
    )
    spec = dvs_factory["dvs"].AddDVPortgroup_Task.call_args.kwargs["spec"][0]
    ranges = spec.defaultPortConfig.vlan.vlanId
    assert [(r.start, r.end) for r in ranges] == [(100, 200), (300, 400)]


def test_reconfigure_vlan_change(dvs_factory, opts):
    pg = _vlan_pg(vlan_id=100)
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    vim_dvs_portgroup.reconfigure(opts, "prod-dvs", "prod-web", vlan_id=200)
    spec = pg.ReconfigureDVPortgroup_Task.call_args.kwargs["spec"]
    assert spec.defaultPortConfig.vlan.vlanId == 200
    assert spec.configVersion == "1"


def test_reconfigure_num_ports_only(dvs_factory, opts):
    pg = _vlan_pg()
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    vim_dvs_portgroup.reconfigure(opts, "prod-dvs", "prod-web", num_ports=32)
    spec = pg.ReconfigureDVPortgroup_Task.call_args.kwargs["spec"]
    assert spec.numPorts == 32
    # defaultPortConfig not touched
    assert spec.defaultPortConfig is None


def test_delete(dvs_factory, opts):
    pg = _vlan_pg()
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    vim_dvs_portgroup.delete(opts, "prod-dvs", "prod-web")
    pg.Destroy_Task.assert_called_once()


def test_get_missing_raises(dvs_factory, opts):
    dvs_factory["dvs"] = _fake_dvs(portgroups=[])
    with pytest.raises(LookupError):
        vim_dvs_portgroup.get(opts, "prod-dvs", "missing")


# ---------- Uplink NIC teaming (physical-uplink failover mode) ----------


def _pg_with_teaming(
    name="prod-web",
    policy="loadbalance_srcid",
    active=("Uplink 1", "Uplink 2"),
    standby=(),
    notify=True,
    check_beacon=False,
):
    pg = _vlan_pg(name=name)
    t = vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortTeamingPolicy(
        inherited=False,
        policy=vim.StringPolicy(inherited=False, value=policy),
        notifySwitches=vim.BoolPolicy(inherited=False, value=notify),
        failureCriteria=vim.dvs.VmwareDistributedVirtualSwitch.FailureCriteria(
            inherited=False,
            checkBeacon=vim.BoolPolicy(inherited=False, value=check_beacon),
        ),
        uplinkPortOrder=vim.dvs.VmwareDistributedVirtualSwitch.UplinkPortOrderPolicy(
            inherited=False,
            activeUplinkPort=list(active),
            standbyUplinkPort=list(standby),
        ),
    )
    pg.config.defaultPortConfig.uplinkTeamingPolicy = t
    return pg


def test_get_teaming_returns_policy(dvs_factory, opts):
    pg = _pg_with_teaming(policy="loadbalance_ip", active=("Uplink 1",), standby=("Uplink 2",))
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    t = vim_dvs_portgroup.get_teaming(opts, "prod-dvs", "prod-web")
    assert t["policy"] == "loadbalance_ip"
    assert t["active_uplinks"] == ["Uplink 1"]
    assert t["standby_uplinks"] == ["Uplink 2"]
    assert t["notify_switches"] is True


def test_set_teaming_builds_spec(dvs_factory, opts):
    pg = _vlan_pg()
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    vim_dvs_portgroup.set_teaming(
        opts,
        "prod-dvs",
        "prod-web",
        policy="loadbalance_loadbased",
        notify_switches=True,
        active_uplinks=["Uplink 1", "Uplink 2"],
        standby_uplinks=[],
        check_beacon=False,
    )
    spec = pg.ReconfigureDVPortgroup_Task.call_args.kwargs["spec"]
    t = spec.defaultPortConfig.uplinkTeamingPolicy
    assert t.policy.value == "loadbalance_loadbased"
    assert t.notifySwitches.value is True
    assert t.uplinkPortOrder.activeUplinkPort == ["Uplink 1", "Uplink 2"]
    assert t.uplinkPortOrder.standbyUplinkPort == []
    assert t.failureCriteria.checkBeacon.value is False
    assert spec.configVersion == pg.config.configVersion


def test_set_teaming_rejects_bad_policy(dvs_factory, opts):
    pg = _vlan_pg()
    dvs_factory["dvs"] = _fake_dvs(portgroups=[pg])
    with pytest.raises(ValueError, match="teaming policy"):
        vim_dvs_portgroup.set_teaming(opts, "prod-dvs", "prod-web", policy="bogus")


def test_list_exposes_teaming_in_dict(dvs_factory, opts):
    dvs_factory["dvs"] = _fake_dvs(
        portgroups=[_pg_with_teaming(policy="loadbalance_srcmac", active=("Uplink 1",))]
    )
    result = vim_dvs_portgroup.list_(opts, "prod-dvs")
    assert result[0]["teaming"]["policy"] == "loadbalance_srcmac"
    assert result[0]["teaming"]["active_uplinks"] == ["Uplink 1"]
