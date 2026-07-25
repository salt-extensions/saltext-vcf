"""Tests for states.vcf_esxi_auth_proxy."""

import pytest

from saltext.vcf.clients import esxi_auth_proxy as client
from saltext.vcf.states import vcf_esxi_auth_proxy as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "current": {
            "cam_address": None,
            "verify_cam_cert": None,
            "joined": False,
            "domain": None,
        },
        "set_calls": [],
        "join_calls": [],
        "leave_calls": [],
    }

    def _get(opts, host, profile=None):
        return dict(state["current"])

    def _set(opts, host, cam_address=None, verify_cam_cert=None, profile=None):
        state["set_calls"].append((host, cam_address, verify_cam_cert))
        if cam_address is not None:
            state["current"]["cam_address"] = cam_address
        if verify_cam_cert is not None:
            state["current"]["verify_cam_cert"] = verify_cam_cert
        return dict(state["current"])

    def _join(opts, host, domain, cam_server, profile=None):
        state["join_calls"].append((host, domain, cam_server))
        state["current"].update({"joined": True, "domain": domain})
        return "task-join-1"

    def _leave(opts, host, force=False, profile=None):
        state["leave_calls"].append((host, force))
        state["current"].update({"joined": False, "domain": None})
        return "task-leave-1"

    monkeypatch.setattr(client, "get_config", _get)
    monkeypatch.setattr(client, "set_config", _set)
    monkeypatch.setattr(client, "join_domain_via_cam", _join)
    monkeypatch.setattr(client, "leave_domain", _leave)
    return state


# ---------------- configured ----------------


def test_configured_applies_both_when_empty(stub):
    ret = st.configured("esxi-01", cam_address="cam.example.com", verify_cam_cert=True)
    assert ret["result"] is True
    assert set(ret["changes"]) == {"cam_address", "verify_cam_cert"}
    assert stub["set_calls"] == [("esxi-01", "cam.example.com", True)]


def test_configured_no_op_when_matching(stub):
    stub["current"]["cam_address"] = "cam.example.com"
    stub["current"]["verify_cam_cert"] = True
    ret = st.configured("esxi-01", cam_address="cam.example.com", verify_cam_cert=True)
    assert ret["changes"] == {}
    assert stub["set_calls"] == []


def test_configured_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.configured("esxi-01", cam_address="cam.example.com", verify_cam_cert=True)
    assert ret["result"] is None
    assert stub["set_calls"] == []


def test_configured_only_updates_diff(stub):
    stub["current"]["cam_address"] = "cam.example.com"
    stub["current"]["verify_cam_cert"] = False
    ret = st.configured("esxi-01", cam_address="cam.example.com", verify_cam_cert=True)
    assert list(ret["changes"]) == ["verify_cam_cert"]
    assert stub["set_calls"] == [("esxi-01", None, True)]


# ---------------- joined ----------------


def test_joined_no_op_when_already_joined_same_domain(stub):
    stub["current"].update({"joined": True, "domain": "corp.example.com"})
    ret = st.joined("esxi-01", domain="corp.example.com", cam_server="cam.example.com")
    assert ret["changes"] == {}
    assert stub["join_calls"] == []


def test_joined_case_insensitive(stub):
    stub["current"].update({"joined": True, "domain": "CORP.EXAMPLE.COM"})
    ret = st.joined("esxi-01", domain="corp.example.com", cam_server="cam.example.com")
    assert ret["changes"] == {}


def test_joined_refuses_switch(stub):
    stub["current"].update({"joined": True, "domain": "other.example.com"})
    ret = st.joined("esxi-01", domain="corp.example.com", cam_server="cam.example.com")
    assert ret["result"] is False
    assert stub["join_calls"] == []


def test_joined_performs_join(stub):
    ret = st.joined("esxi-01", domain="corp.example.com", cam_server="cam.example.com")
    assert ret["result"] is True
    assert stub["join_calls"] == [("esxi-01", "corp.example.com", "cam.example.com")]
    assert ret["changes"]["task"] == "task-join-1"


def test_joined_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.joined("esxi-01", domain="corp.example.com", cam_server="cam.example.com")
    assert ret["result"] is None
    assert stub["join_calls"] == []


# ---------------- left ----------------


def test_left_no_op_when_not_joined(stub):
    ret = st.left("esxi-01")
    assert ret["changes"] == {}
    assert stub["leave_calls"] == []


def test_left_performs_leave(stub):
    stub["current"].update({"joined": True, "domain": "corp.example.com"})
    ret = st.left("esxi-01", force=True)
    assert ret["result"] is True
    assert stub["leave_calls"] == [("esxi-01", True)]
    assert ret["changes"]["joined"]["old"] == "corp.example.com"


def test_left_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["current"].update({"joined": True, "domain": "corp.example.com"})
    ret = st.left("esxi-01")
    assert ret["result"] is None
    assert stub["leave_calls"] == []
