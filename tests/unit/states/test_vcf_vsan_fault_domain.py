"""Tests for states.vcf_vsan_fault_domain."""

import pytest

from saltext.vcf.clients import vsan_fault_domain as c
from saltext.vcf.states import vcf_vsan_fault_domain as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": [], "assigned": []}
    monkeypatch.setattr(c, "list_", lambda opts, name, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "assign",
        lambda opts, name, mapping, profile=None: (
            state["assigned"].append((name, mapping)) or "task-2"
        ),
    )
    return state


def test_no_change_when_matches(stub):
    stub["current"] = [
        {"host": "esx-0-00", "host_id": "host-1", "fault_domain": "rack-A"},
        {"host": "esx-0-01", "host_id": "host-2", "fault_domain": "rack-B"},
    ]
    ret = st.member("domain-c9", {"esx-0-00": "rack-A", "esx-0-01": "rack-B"})
    assert ret["changes"] == {}
    assert not stub["assigned"]


def test_drift_triggers_assign(stub):
    stub["current"] = [
        {"host": "esx-0-00", "host_id": "host-1", "fault_domain": "rack-A"},
        {"host": "esx-0-01", "host_id": "host-2", "fault_domain": "rack-A"},
    ]
    ret = st.member("domain-c9", {"esx-0-00": "rack-A", "esx-0-01": "rack-B"})
    assert "esx-0-01" in ret["changes"]
    assert ret["changes"]["esx-0-01"]["new"] == "rack-B"
    assert ret["changes"]["task_id"] == "task-2"


def test_lookup_by_host_id(stub):
    stub["current"] = [{"host": "esx-0-00", "host_id": "host-1", "fault_domain": "rack-A"}]
    ret = st.member("domain-c9", {"host-1": "rack-A"})
    assert ret["changes"] == {}


def test_test_mode(monkeypatch, stub):
    stub["current"] = [{"host": "esx-0-00", "host_id": "host-1", "fault_domain": "rack-A"}]
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.member("domain-c9", {"esx-0-00": "rack-B"})
    assert ret["result"] is None
    assert not stub["assigned"]
