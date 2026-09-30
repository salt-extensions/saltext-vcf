"""Tests for the upgraded vmkernel_present state + vmotion_configured."""

import pytest

from saltext.vcf.clients import vim_host_network as c
from saltext.vcf.clients import vim_host_vmotion as vm_c
from saltext.vcf.states import vcf_vim_host_network as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _existing_vmk(**over):
    out = {
        "device": "vmk1",
        "portgroup": "vMotion",
        "mac_address": "00:50:56",
        "mtu": 1500,
        "dhcp": False,
        "ip_address": "10.0.0.5",
        "subnet_mask": "255.255.255.0",
    }
    out.update(over)
    return out


def test_vmkernel_present_adds_with_gateway_and_stack(monkeypatch):
    monkeypatch.setattr(c, "vmkernel_get_or_none", lambda o, h, d, profile=None: None)
    calls = {}

    def _add(o, h, pg, **kw):
        calls.update(pg=pg, **kw)
        return "vmk2"

    tt_calls = []
    monkeypatch.setattr(
        c,
        "vmkernel_set_traffic_types",
        lambda o, h, d, tt, profile=None: tt_calls.append((d, tt)),
    )
    monkeypatch.setattr(c, "vmkernel_add", _add)
    ret = st.vmkernel_present(
        "vmk2",
        "esxi-01",
        portgroup="vMotion",
        ip_address="10.0.0.6",
        subnet_mask="255.255.255.0",
        tcpip_stack="vmotion",
        default_gateway="10.0.0.1",
        traffic_types={"vmotion": True},
    )
    assert ret["changes"] == {"new": "vmk2"}
    assert calls["tcpip_stack"] == "vmotion"
    assert calls["default_gateway"] == "10.0.0.1"
    assert tt_calls == [("vmk2", {"vmotion": True})]


def test_vmkernel_present_existing_updates_gateway(monkeypatch):
    monkeypatch.setattr(c, "vmkernel_get_or_none", lambda o, h, d, profile=None: _existing_vmk())
    captured = {}
    monkeypatch.setattr(c, "vmkernel_update", lambda o, h, d, **kw: captured.update(kw))
    ret = st.vmkernel_present("vmk1", "esxi-01", portgroup="vMotion", default_gateway="10.0.0.254")
    assert ret["changes"]["default_gateway"] == ("(existing)", "10.0.0.254")
    assert captured["default_gateway"] == "10.0.0.254"


def test_vmkernel_present_vsan_wiring(monkeypatch):
    monkeypatch.setattr(c, "vmkernel_get_or_none", lambda o, h, d, profile=None: _existing_vmk())
    vsan_calls = []
    monkeypatch.setattr(
        c, "vmkernel_vsan", lambda o, h, d, e, profile=None: vsan_calls.append((d, e)) or True
    )
    ret = st.vmkernel_present("vmk1", "esxi-01", portgroup="vMotion", enable_vsan=True)
    assert ret["changes"]["vsan"] == (False, True)
    assert vsan_calls == [("vmk1", True)]


def test_vmkernel_present_vsan_already_wired(monkeypatch):
    monkeypatch.setattr(c, "vmkernel_get_or_none", lambda o, h, d, profile=None: _existing_vmk())
    monkeypatch.setattr(c, "vmkernel_vsan", lambda o, h, d, e, profile=None: False)
    ret = st.vmkernel_present("vmk1", "esxi-01", portgroup="vMotion", enable_vsan=True)
    assert "vsan" not in ret["changes"]


def test_vmotion_configured_enable(monkeypatch):
    monkeypatch.setattr(vm_c, "get_enabled", lambda o, h, profile=None: {"enabled": False, "device": None})
    monkeypatch.setattr(vm_c, "enable", lambda o, h, d, profile=None: None)
    ret = st.vmotion_configured("vmotion", "esxi-01", True, device="vmk1")
    assert ret["changes"]["enabled"] == (False, True)
    assert ret["changes"]["device"] == (None, "vmk1")


def test_vmotion_configured_noop(monkeypatch):
    monkeypatch.setattr(vm_c, "get_enabled", lambda o, h, profile=None: {"enabled": True, "device": "vmk1"})
    ret = st.vmotion_configured("vmotion", "esxi-01", True, device="vmk1")
    assert ret["changes"] == {}


def test_vmotion_configured_test_mode(monkeypatch):
    monkeypatch.setattr(vm_c, "get_enabled", lambda o, h, profile=None: {"enabled": False, "device": None})
    monkeypatch.setattr(vm_c, "enable", lambda *a, **kw: pytest.fail("must not enable"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.vmotion_configured("vmotion", "esxi-01", True, device="vmk1")
    assert ret["result"] is None
