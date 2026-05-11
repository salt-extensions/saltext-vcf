"""Tests for states.vmware_cluster_config."""

import pytest

from saltext.vmware.clients import cluster_config as c
from saltext.vmware.states import vmware_cluster_config as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "enablement": {"enabled": True},
        "config": None,
        "draft_id": "draft-1",
        "patches": [],
        "applied": [],
    }

    monkeypatch.setattr(c, "enablement_get", lambda opts, name, profile=None: state["enablement"])
    monkeypatch.setattr(c, "configuration_get", lambda opts, name, profile=None: state["config"])
    monkeypatch.setattr(
        c, "draft_create", lambda opts, name, body=None, profile=None: state["draft_id"]
    )
    monkeypatch.setattr(
        c,
        "draft_get_configuration",
        lambda opts, name, d, profile=None: (
            {} if state["config"] is None else dict(state["config"])
        ),
    )
    monkeypatch.setattr(
        c,
        "draft_update_configuration",
        lambda opts, name, d, body, profile=None: state["patches"].append((d, body)),
    )
    monkeypatch.setattr(
        c,
        "draft_apply",
        lambda opts, name, d, profile=None: state["applied"].append((name, d)),
    )
    return state


def test_enabled_when_enabled(stub):
    stub["enablement"] = {"enabled": True}
    ret = st.enabled("domain-c9")
    assert ret["result"] is True
    assert ret["changes"] == {}


def test_enabled_reports_failure_when_disabled(stub):
    stub["enablement"] = {"enabled": False}
    ret = st.enabled("domain-c9")
    assert ret["result"] is False
    assert "not enabled" in ret["comment"]


def test_profile_value_no_change(stub):
    stub["config"] = {"profile": {"esx": {"health": {"ntp_health": {"servers": ["a"]}}}}}
    ret = st.profile_value("domain-c9", "profile.esx.health.ntp_health.servers", ["a"])
    assert ret["changes"] == {}
    assert stub["patches"] == []
    assert stub["applied"] == []


def test_profile_value_creates_draft_and_applies(stub):
    stub["config"] = {"profile": {"esx": {"health": {"ntp_health": {"servers": ["old"]}}}}}
    ret = st.profile_value("domain-c9", "profile.esx.health.ntp_health.servers", ["new1", "new2"])
    assert ret["result"] is True
    assert ret["changes"] == {
        "profile.esx.health.ntp_health.servers": {
            "old": ["old"],
            "new": ["new1", "new2"],
        }
    }
    assert len(stub["patches"]) == 1
    assert stub["applied"] == [("domain-c9", "draft-1")]


def test_profile_value_test_mode(monkeypatch, stub):
    stub["config"] = {"profile": {"esx": {"health": {}}}}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.profile_value("domain-c9", "profile.esx.health.ntp_health.servers", ["x"])
    assert ret["result"] is None
    assert stub["patches"] == []
    assert stub["applied"] == []


def test_profile_value_fails_when_no_config(stub):
    stub["config"] = None  # cluster not vLCM-managed
    ret = st.profile_value("domain-c9", "profile.x", 1)
    assert ret["result"] is False
    assert "vLCM-managed" in ret["comment"]
