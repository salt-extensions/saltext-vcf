"""Tests for states.vcf_sddc_ceip."""

import pytest

from saltext.vcf.clients import sddc_ceip as c
from saltext.vcf.clients import sddc_tasks
from saltext.vcf.states import vcf_sddc_ceip as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "ceip": {"status": "ENABLED", "instanceId": "abc"},
        "set_calls": [],
        "wait_calls": [],
        "wait_should_raise": None,
        # allow tests to change the reported state on the second read (post-PATCH)
        "post_patch_status": None,
    }

    def _get(_opts, profile=None):
        return state["ceip"]

    def _set(_opts, enabled, profile=None):
        state["set_calls"].append(bool(enabled))
        # transition to ...ING
        state["ceip"] = {
            "status": "ENABLING" if enabled else "DISABLING",
            "instanceId": "abc",
        }
        return {"id": "task-xyz", "status": "IN_PROGRESS"}

    def _wait(_opts, task_id, timeout=3600, poll_interval=10, profile=None):
        state["wait_calls"].append(task_id)
        exc = state["wait_should_raise"]
        if exc is not None:
            raise exc
        # simulate settled state
        state["ceip"] = {
            "status": state["post_patch_status"] or "ENABLED",
            "instanceId": "abc",
        }
        return state["ceip"]

    monkeypatch.setattr(c, "get", _get)
    monkeypatch.setattr(c, "set_", _set)
    monkeypatch.setattr(sddc_tasks, "wait", _wait)
    return state


def test_enabled_no_change_when_already_enabled(stub):
    stub["ceip"] = {"status": "ENABLED", "instanceId": "x"}
    ret = st.enabled("name")
    assert ret["changes"] == {}
    assert ret["result"] is True
    assert stub["set_calls"] == []


def test_disabled_no_change_when_already_disabled(stub):
    stub["ceip"] = {"status": "DISABLED", "instanceId": "x"}
    ret = st.disabled("name")
    assert ret["changes"] == {}
    assert stub["set_calls"] == []


def test_disabled_flips_from_enabled_and_waits(stub):
    stub["ceip"] = {"status": "ENABLED", "instanceId": "x"}
    stub["post_patch_status"] = "DISABLED"
    ret = st.disabled("name")
    assert stub["set_calls"] == [False]
    assert stub["wait_calls"] == ["task-xyz"]
    assert ret["changes"] == {"status": {"old": "ENABLED", "new": "DISABLED"}}
    assert ret["result"] is True


def test_enabled_flips_from_disabled_and_waits(stub):
    stub["ceip"] = {"status": "DISABLED", "instanceId": "x"}
    stub["post_patch_status"] = "ENABLED"
    ret = st.enabled("name")
    assert stub["set_calls"] == [True]
    assert stub["wait_calls"] == ["task-xyz"]
    assert ret["changes"] == {"status": {"old": "DISABLED", "new": "ENABLED"}}


def test_disabled_no_wait(stub):
    stub["ceip"] = {"status": "ENABLED", "instanceId": "x"}
    ret = st.disabled("name", wait=False)
    assert stub["set_calls"] == [False]
    assert stub["wait_calls"] == []
    assert ret["changes"]["status"]["new"] == "DISABLED"


def test_disabled_test_mode(monkeypatch, stub):
    stub["ceip"] = {"status": "ENABLED", "instanceId": "x"}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.disabled("name")
    assert ret["result"] is None
    assert stub["set_calls"] == []
    assert "would change" in ret["comment"]


def test_disabled_leaves_in_flight_transition_alone(stub):
    stub["ceip"] = {"status": "DISABLING", "instanceId": "x"}
    ret = st.disabled("name")
    assert ret["result"] is True
    assert stub["set_calls"] == []
    assert "in-flight" in ret["comment"] or "DISABLING" in ret["comment"]


def test_disabled_reports_task_failure(stub):
    stub["ceip"] = {"status": "ENABLED", "instanceId": "x"}
    stub["wait_should_raise"] = RuntimeError("SDDC task failed at ESXi step")
    ret = st.disabled("name")
    assert ret["result"] is False
    assert "did not complete" in ret["comment"]


def test_disabled_reports_task_timeout(stub):
    stub["ceip"] = {"status": "ENABLED", "instanceId": "x"}
    stub["wait_should_raise"] = TimeoutError("still IN_PROGRESS after 60s")
    ret = st.disabled("name", timeout=60)
    assert ret["result"] is False
    assert "did not complete" in ret["comment"]
