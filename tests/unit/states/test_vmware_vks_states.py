"""Tests for the VKS-extension state modules."""

import pytest

from saltext.vmware.clients import sddc_vcf_services as svc_c
from saltext.vmware.clients import vcenter_supervisor_service as svcsv_c
from saltext.vmware.clients import vcenter_vm_class as vmc_c
from saltext.vmware.states import vmware_vcenter_supervisor_service as svc_state
from saltext.vmware.states import vmware_vcenter_vm_class as vmc_state
from saltext.vmware.states import vmware_vcf_services as vcfs_state


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (svc_state, vmc_state, vcfs_state):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


@pytest.fixture
def vmc_stub(monkeypatch):
    state = {"existing": None, "created": [], "updated": [], "deleted": []}
    monkeypatch.setattr(vmc_c, "get_or_none", lambda opts, cid, profile=None: state["existing"])
    monkeypatch.setattr(
        vmc_c, "create", lambda opts, spec, profile=None: state["created"].append(spec)
    )
    monkeypatch.setattr(
        vmc_c,
        "update",
        lambda opts, cid, spec, profile=None: state["updated"].append((cid, spec)),
    )
    monkeypatch.setattr(
        vmc_c, "delete", lambda opts, cid, profile=None: state["deleted"].append(cid)
    )
    return state


def test_vm_class_present_creates(vmc_stub):
    ret = vmc_state.present("my-class", cpu_count=4, memory_MB=8192, description="x")
    assert ret["changes"] == {"new": "my-class"}
    assert vmc_stub["created"][0]["cpu_count"] == 4
    assert vmc_stub["created"][0]["description"] == "x"


def test_vm_class_present_already_matching(vmc_stub):
    vmc_stub["existing"] = {"id": "my", "cpu_count": 2, "memory_MB": 4096}
    ret = vmc_state.present("my", cpu_count=2, memory_MB=4096)
    assert ret["changes"] == {}
    assert "matches" in ret["comment"]


def test_vm_class_present_updates_on_drift(vmc_stub):
    vmc_stub["existing"] = {"id": "my", "cpu_count": 2, "memory_MB": 4096}
    ret = vmc_state.present("my", cpu_count=4, memory_MB=4096)
    assert "cpu_count" in ret["changes"]["updated"]
    assert vmc_stub["updated"][0][0] == "my"
    assert vmc_stub["updated"][0][1]["cpu_count"] == 4


def test_vm_class_present_test_mode(monkeypatch, vmc_stub):
    monkeypatch.setattr(vmc_state, "__opts__", {"test": True}, raising=False)
    ret = vmc_state.present("my", cpu_count=4, memory_MB=8192)
    assert ret["result"] is None
    assert vmc_stub["created"] == []


def test_vm_class_absent(vmc_stub):
    vmc_stub["existing"] = {"id": "my"}
    ret = vmc_state.absent("my")
    assert ret["changes"] == {"deleted": "my"}
    assert vmc_stub["deleted"] == ["my"]


def test_vm_class_absent_already_gone(vmc_stub):
    ret = vmc_state.absent("my")
    assert ret["changes"] == {}


@pytest.fixture
def svc_stub(monkeypatch):
    state = {"svc": None, "actions": []}
    monkeypatch.setattr(svcsv_c, "get_or_none", lambda opts, sid, profile=None: state["svc"])
    monkeypatch.setattr(
        svcsv_c,
        "activate",
        lambda opts, sid, profile=None: state["actions"].append(("a", sid)),
    )
    monkeypatch.setattr(
        svcsv_c,
        "deactivate",
        lambda opts, sid, profile=None: state["actions"].append(("d", sid)),
    )
    monkeypatch.setattr(
        svcsv_c,
        "delete",
        lambda opts, sid, profile=None: state["actions"].append(("x", sid)),
    )
    return state


def test_supervisor_service_activated_when_already(svc_stub):
    svc_stub["svc"] = {"state": "ACTIVATED"}
    assert svc_state.activated("tkg")["changes"] == {}


def test_supervisor_service_activated_transitions(svc_stub):
    svc_stub["svc"] = {"state": "DEACTIVATED"}
    ret = svc_state.activated("tkg")
    assert ret["changes"] == {"state": ("DEACTIVATED", "ACTIVATED")}
    assert svc_stub["actions"] == [("a", "tkg")]


def test_supervisor_service_activated_missing(svc_stub):
    ret = svc_state.activated("tkg")
    assert ret["result"] is False


def test_supervisor_service_deactivated_transitions(svc_stub):
    svc_stub["svc"] = {"state": "ACTIVATED"}
    ret = svc_state.deactivated("tkg")
    assert ret["changes"] == {"state": ("ACTIVATED", "DEACTIVATED")}


def test_supervisor_service_absent(svc_stub):
    svc_stub["svc"] = {"state": "ACTIVATED"}
    ret = svc_state.absent("tkg")
    assert ret["changes"] == {"deleted": "tkg"}


def test_supervisor_service_absent_already_gone(svc_stub):
    assert svc_state.absent("tkg")["changes"] == {}


@pytest.fixture
def vcfs_stub(monkeypatch):
    state = {"svc": None}
    monkeypatch.setattr(svc_c, "get_by_name", lambda opts, name, profile=None: state["svc"])
    return state


def test_vcf_services_healthy_up(vcfs_stub):
    vcfs_stub["svc"] = {"status": "UP", "version": "9.2"}
    ret = vcfs_state.healthy("COMMON_SERVICES")
    assert ret["result"] is True


def test_vcf_services_healthy_down(vcfs_stub):
    vcfs_stub["svc"] = {"status": "DOWN"}
    ret = vcfs_state.healthy("LCM")
    assert ret["result"] is False


def test_vcf_services_healthy_missing(vcfs_stub):
    ret = vcfs_state.healthy("MISSING")
    assert ret["result"] is False
