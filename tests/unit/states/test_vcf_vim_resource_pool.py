"""Tests for the vim_resource_pool state module."""

import pytest

from saltext.vcf.clients import vim_resource_pool as c
from saltext.vcf.states import vcf_vim_resource_pool as st


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
    monkeypatch.setattr(c, "get_shares", lambda o, r, profile=None: _shares())
    ret = st.shares("rp-1", cpu={"shares_level": "normal"})
    assert ret["changes"] == {}


def test_cpu_drift_applied(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_shares", lambda o, r, profile=None: _shares())
    monkeypatch.setattr(c, "set_shares", lambda *a, **kw: calls.append(kw) or None)
    ret = st.shares("rp-1", cpu={"shares_level": "high"})
    assert ret["changes"]["cpu"]["shares_level"] == ("normal", "high")
    assert calls[0]["cpu"] == {"shares_level": "high"}


def test_both_cpu_and_memory_drift(monkeypatch):
    monkeypatch.setattr(c, "get_shares", lambda o, r, profile=None: _shares())
    monkeypatch.setattr(c, "set_shares", lambda *a, **kw: None)
    ret = st.shares("rp-1", cpu={"limit": 1000}, memory={"reservation": 512})
    assert "cpu" in ret["changes"]
    assert "memory" in ret["changes"]


def test_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "get_shares", lambda o, r, profile=None: _shares())
    monkeypatch.setattr(c, "set_shares", lambda *a, **kw: pytest.fail("should not write"))
    ret = st.shares("rp-1", cpu={"shares_level": "high"})
    assert ret["result"] is None
