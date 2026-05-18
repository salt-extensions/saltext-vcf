"""Tests for states.vcf_vsan_cluster."""

import pytest

from saltext.vcf.clients import vsan_cluster as c
from saltext.vcf.states import vcf_vsan_cluster as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": {}, "reconfigured": []}
    monkeypatch.setattr(c, "get", lambda opts, name, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "reconfigure",
        lambda opts, name, profile=None, **kwargs: (
            state["reconfigured"].append((name, kwargs)) or "task-1"
        ),
    )
    return state


def test_no_change_when_matches(stub):
    stub["current"] = {"enabled": True, "dedup_compression_enabled": True}
    ret = st.configured("domain-c9", enabled=True, dedup_compression_enabled=True)
    assert ret["changes"] == {}
    assert not stub["reconfigured"]


def test_drift_triggers_reconfigure(stub):
    stub["current"] = {"enabled": True, "dedup_compression_enabled": False}
    ret = st.configured("domain-c9", dedup_compression_enabled=True)
    assert "dedup_compression_enabled" in ret["changes"]
    assert ret["changes"]["task_id"] == "task-1"
    assert stub["reconfigured"][0][0] == "domain-c9"


def test_test_mode_does_not_reconfigure(monkeypatch, stub):
    stub["current"] = {"enabled": False}
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.configured("domain-c9", enabled=True)
    assert ret["result"] is None
    assert not stub["reconfigured"]


def test_unspecified_fields_not_in_drift(stub):
    stub["current"] = {"enabled": True, "encryption_enabled": False}
    # Only specify dedup; encryption shouldn't drift even though it's False.
    ret = st.configured("domain-c9", dedup_compression_enabled=True)
    assert "encryption_enabled" not in ret["changes"]
