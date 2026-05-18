"""Tests for the VDS + DPG state module."""

import pytest

from saltext.vcf.clients import vim_dvs as dvs_c
from saltext.vcf.clients import vim_dvs_portgroup as pg_c
from saltext.vcf.states import vcf_vim_dvs as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


# ---------- present / absent for VDS ----------


def test_dvs_present_creates(monkeypatch):
    actions = {"created": []}
    monkeypatch.setattr(dvs_c, "get_or_none", lambda o, n, profile=None: None)
    monkeypatch.setattr(
        dvs_c,
        "create",
        lambda o, n, dc, **kw: actions["created"].append((n, dc, kw)),
    )
    ret = st.present("prod-dvs", datacenter="Datacenter", max_mtu=9000)
    assert ret["changes"] == {"new": "prod-dvs"}
    assert actions["created"][0][1] == "Datacenter"
    assert actions["created"][0][2]["max_mtu"] == 9000


def test_dvs_present_already_matches(monkeypatch):
    monkeypatch.setattr(
        dvs_c,
        "get_or_none",
        lambda o, n, profile=None: {"name": n, "max_mtu": 1500},
    )
    ret = st.present("prod-dvs", datacenter="Datacenter", max_mtu=1500)
    assert ret["changes"] == {}
    assert "already matches" in ret["comment"]


def test_dvs_present_updates_on_mtu_drift(monkeypatch):
    actions = {"reconfigured": []}
    monkeypatch.setattr(
        dvs_c,
        "get_or_none",
        lambda o, n, profile=None: {"name": n, "max_mtu": 1500},
    )
    monkeypatch.setattr(
        dvs_c,
        "reconfigure",
        lambda o, n, max_mtu=None, description=None, profile=None: actions["reconfigured"].append(
            (n, max_mtu)
        ),
    )
    ret = st.present("prod-dvs", datacenter="Datacenter", max_mtu=9000)
    assert ret["changes"]["max_mtu"] == (1500, 9000)
    assert actions["reconfigured"][0] == ("prod-dvs", 9000)


def test_dvs_absent_when_present(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(dvs_c, "get_or_none", lambda o, n, profile=None: {"name": n})
    monkeypatch.setattr(dvs_c, "delete", lambda o, n, profile=None: actions["deleted"].append(n))
    ret = st.absent("prod-dvs")
    assert ret["changes"] == {"deleted": "prod-dvs"}


def test_dvs_absent_when_missing(monkeypatch):
    monkeypatch.setattr(dvs_c, "get_or_none", lambda o, n, profile=None: None)
    ret = st.absent("prod-dvs")
    assert ret["changes"] == {}


def test_dvs_present_test_mode(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", {**opts, "test": True}, raising=False)
    monkeypatch.setattr(dvs_c, "get_or_none", lambda o, n, profile=None: None)
    ret = st.present("prod-dvs", datacenter="Datacenter")
    assert ret["result"] is None
    assert "would be created" in ret["comment"]


# ---------- portgroup states ----------


def test_portgroup_present_creates(monkeypatch):
    actions = {"created": []}
    monkeypatch.setattr(pg_c, "get_or_none", lambda o, d, n, profile=None: None)
    monkeypatch.setattr(
        pg_c,
        "create_vlan",
        lambda o, d, n, **kw: actions["created"].append((d, n, kw)),
    )
    ret = st.portgroup_present("prod-web", dvs="prod-dvs", vlan_id=100, num_ports=16)
    assert ret["changes"] == {"new": "prod-web"}
    assert actions["created"][0][2]["vlan_id"] == 100


def test_portgroup_present_already_matches(monkeypatch):
    monkeypatch.setattr(
        pg_c,
        "get_or_none",
        lambda o, d, n, profile=None: {
            "name": n,
            "num_ports": 16,
            "vlan": {"kind": "vlan", "vlan_id": 100},
        },
    )
    ret = st.portgroup_present("prod-web", dvs="prod-dvs", vlan_id=100, num_ports=16)
    assert ret["changes"] == {}


def test_portgroup_present_updates_vlan(monkeypatch):
    actions = {"reconfigured": []}
    monkeypatch.setattr(
        pg_c,
        "get_or_none",
        lambda o, d, n, profile=None: {
            "name": n,
            "num_ports": 16,
            "vlan": {"kind": "vlan", "vlan_id": 100},
        },
    )
    monkeypatch.setattr(
        pg_c,
        "reconfigure",
        lambda o, d, n, **kw: actions["reconfigured"].append((d, n, kw)),
    )
    ret = st.portgroup_present("prod-web", dvs="prod-dvs", vlan_id=200, num_ports=16)
    assert "vlan_id" in ret["changes"]
    assert actions["reconfigured"][0][2]["vlan_id"] == 200


def test_portgroup_absent_when_present(monkeypatch):
    actions = {"deleted": []}
    monkeypatch.setattr(pg_c, "get_or_none", lambda o, d, n, profile=None: {"name": n})
    monkeypatch.setattr(
        pg_c,
        "delete",
        lambda o, d, n, profile=None: actions["deleted"].append((d, n)),
    )
    ret = st.portgroup_absent("prod-web", dvs="prod-dvs")
    assert ret["changes"] == {"deleted": "prod-web"}
