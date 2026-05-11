"""Tests for clients.vim_dvs_portgroup (DPG lifecycle via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_dvs_portgroup


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
