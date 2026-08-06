"""Tests for the vccluster_resource_pool state module."""

import pytest

from saltext.vcf.clients import vccluster_resource_pool as c
from saltext.vcf.states import vcf_vccluster_resource_pool as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _shares(level="normal", value=4000, reservation=0, limit=-1):
    return {
        "cpu": {
            "reservation": reservation,
            "expandable_reservation": True,
            "limit": limit,
            "shares_level": level,
            "shares_value": value,
        },
        "memory": {
            "reservation": 0,
            "expandable_reservation": True,
            "limit": -1,
            "shares_level": "normal",
            "shares_value": 163840,
        },
    }


def test_already_matches(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: "rp-1")
    monkeypatch.setattr(c, "get_shares", lambda o, cluster, name, profile=None: _shares())
    ret = st.present("Production", "cluster-1", cpu={"shares_level": "normal"})
    assert ret["changes"] == {}


def test_creates_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: None)
    monkeypatch.setattr(
        c, "create", lambda o, cluster, name, profile=None: calls.append((cluster, name))
    )
    monkeypatch.setattr(c, "get_shares", lambda o, cluster, name, profile=None: _shares())
    ret = st.present("Production", "cluster-1", cpu={"shares_level": "normal"})
    assert calls == [("cluster-1", "Production")]
    assert ret["changes"] == {"new": "Production"}


def test_creates_and_applies_shares_when_missing(monkeypatch):
    set_calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: None)
    monkeypatch.setattr(c, "create", lambda o, cluster, name, profile=None: None)
    monkeypatch.setattr(c, "get_shares", lambda o, cluster, name, profile=None: _shares())
    monkeypatch.setattr(
        c,
        "set_shares",
        lambda o, cluster, name, cpu=None, memory=None, profile=None: set_calls.append(cpu),
    )
    ret = st.present("Production", "cluster-1", cpu={"shares_level": "high"})
    assert set_calls == [{"shares_level": "high"}]
    assert ret["changes"]["new"] == "Production"
    assert ret["changes"]["cpu"]["shares_level"] == ("normal", "high")


def test_cpu_drift_applied_when_already_present(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: "rp-1")
    monkeypatch.setattr(c, "get_shares", lambda o, cluster, name, profile=None: _shares())
    monkeypatch.setattr(
        c, "set_shares", lambda o, cluster, name, cpu=None, memory=None, profile=None: calls.append(cpu)
    )
    ret = st.present("Production", "cluster-1", cpu={"shares_level": "high"})
    assert ret["changes"]["cpu"]["shares_level"] == ("normal", "high")
    assert calls[0] == {"shares_level": "high"}


def test_both_cpu_and_memory_drift(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: "rp-1")
    monkeypatch.setattr(c, "get_shares", lambda o, cluster, name, profile=None: _shares())
    monkeypatch.setattr(c, "set_shares", lambda *a, **kw: None)
    ret = st.present("Production", "cluster-1", cpu={"limit": 1000}, memory={"reservation": 512})
    assert "cpu" in ret["changes"]
    assert "memory" in ret["changes"]


def test_test_mode_when_missing(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: None)
    monkeypatch.setattr(c, "create", lambda *a, **kw: pytest.fail("should not create"))
    ret = st.present("Production", "cluster-1", cpu={"shares_level": "high"})
    assert ret["result"] is None


def test_test_mode_when_drift(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: "rp-1")
    monkeypatch.setattr(c, "get_shares", lambda o, cluster, name, profile=None: _shares())
    monkeypatch.setattr(c, "set_shares", lambda *a, **kw: pytest.fail("should not write"))
    ret = st.present("Production", "cluster-1", cpu={"shares_level": "high"})
    assert ret["result"] is None


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: None)
    ret = st.absent("Production", "cluster-1")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: "rp-1")
    monkeypatch.setattr(
        c, "delete", lambda o, cluster, name, profile=None: calls.append((cluster, name))
    )
    ret = st.absent("Production", "cluster-1")
    assert ret["changes"] == {"deleted": "Production"}
    assert calls == [("cluster-1", "Production")]


def test_absent_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get_or_none", lambda o, cluster, name, profile=None: "rp-1")
    monkeypatch.setattr(c, "delete", lambda *a, **kw: pytest.fail("should not delete"))
    ret = st.absent("Production", "cluster-1")
    assert ret["result"] is None
