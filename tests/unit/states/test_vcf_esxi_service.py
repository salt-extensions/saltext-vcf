"""Tests for states.vcf_esxi_service."""

import pytest

from saltext.vcf.clients import esxi_service as c
from saltext.vcf.states import vcf_esxi_service as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"svc": None, "calls": []}

    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: state["svc"])
    monkeypatch.setattr(
        c,
        "start",
        lambda opts, name, profile=None: state["calls"].append(("start", name)),
    )
    monkeypatch.setattr(
        c,
        "stop",
        lambda opts, name, profile=None: state["calls"].append(("stop", name)),
    )
    monkeypatch.setattr(
        c,
        "set_policy",
        lambda opts, name, policy, profile=None: state["calls"].append(("policy", name, policy)),
    )
    return state


def test_running_already(stub):
    stub["svc"] = {"state": "RUNNING", "startup_policy": "ON"}
    ret = st.running("TSM-SSH")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_running_starts(stub):
    stub["svc"] = {"state": "STOPPED", "startup_policy": "ON"}
    ret = st.running("TSM-SSH")
    assert ret["changes"]["state"]["new"] == "RUNNING"
    assert stub["calls"] == [("start", "TSM-SSH")]


def test_running_starts_and_sets_policy(stub):
    stub["svc"] = {"state": "STOPPED", "startup_policy": "OFF"}
    ret = st.running("TSM-SSH", policy="ON")
    assert ret["changes"]["state"]["new"] == "RUNNING"
    assert ret["changes"]["startup_policy"]["new"] == "ON"
    assert ("start", "TSM-SSH") in stub["calls"]
    assert ("policy", "TSM-SSH", "ON") in stub["calls"]


def test_running_missing_service(stub):
    stub["svc"] = None
    ret = st.running("nope")
    assert ret["result"] is False


def test_running_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["svc"] = {"state": "STOPPED", "startup_policy": "ON"}
    ret = st.running("TSM-SSH")
    assert ret["result"] is None
    assert stub["calls"] == []


def test_stopped_already(stub):
    stub["svc"] = {"state": "STOPPED", "startup_policy": "OFF"}
    ret = st.stopped("TSM-SSH")
    assert ret["changes"] == {}


def test_stopped_stops(stub):
    stub["svc"] = {"state": "RUNNING", "startup_policy": "ON"}
    ret = st.stopped("TSM-SSH")
    assert ret["changes"]["state"]["new"] == "STOPPED"
    assert ("stop", "TSM-SSH") in stub["calls"]


def test_policy_change(stub):
    stub["svc"] = {"state": "RUNNING", "startup_policy": "ON"}
    ret = st.policy("TSM-SSH", "OFF")
    assert ret["changes"]["startup_policy"] == {"old": "ON", "new": "OFF"}
    assert ("policy", "TSM-SSH", "OFF") in stub["calls"]


def test_policy_noop(stub):
    stub["svc"] = {"state": "RUNNING", "startup_policy": "ON"}
    ret = st.policy("TSM-SSH", "ON")
    assert ret["changes"] == {}
