"""Tests for the vim_host_powermgmt state module."""

import pytest

from saltext.vcf.clients import vim_host_powermgmt as c
from saltext.vcf.states import vcf_vim_host_powermgmt as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_policy_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_policy",
        lambda o, h, profile=None: {
            "key": 2,
            "short_name": "balanced",
            "name": "Balanced",
            "description": "",
        },
    )
    ret = st.policy("esx-1", policy_key=2)
    assert ret["changes"] == {}


def test_policy_drift_applies(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "get_policy",
        lambda o, h, profile=None: {
            "key": 2,
            "short_name": "balanced",
            "name": "B",
            "description": "",
        },
    )
    monkeypatch.setattr(
        c,
        "set_policy",
        lambda o, h, k, profile=None: calls.append(k)
        or {"key": k, "short_name": "high-performance", "name": "HP", "description": ""},
    )
    ret = st.policy("esx-1", policy_key=1)
    assert calls == [1]
    assert ret["changes"]["policy_key"] == (2, 1)


def test_policy_short_name_lookup(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_policy",
        lambda o, h, profile=None: {
            "key": 2,
            "short_name": "balanced",
            "name": "B",
            "description": "",
        },
    )
    monkeypatch.setattr(
        c,
        "list_policies",
        lambda o, h, profile=None: [
            {"key": 1, "short_name": "high-performance", "name": "HP", "description": ""},
            {"key": 2, "short_name": "balanced", "name": "B", "description": ""},
        ],
    )
    monkeypatch.setattr(
        c,
        "set_policy",
        lambda o, h, k, profile=None: {
            "key": k,
            "short_name": "high-performance",
            "name": "HP",
            "description": "",
        },
    )
    ret = st.policy("esx-1", short_name="high-performance")
    assert ret["changes"]["policy_key"] == (2, 1)


def test_policy_short_name_not_found(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_policy",
        lambda o, h, profile=None: {
            "key": 2,
            "short_name": "balanced",
            "name": "B",
            "description": "",
        },
    )
    monkeypatch.setattr(c, "list_policies", lambda o, h, profile=None: [])
    ret = st.policy("esx-1", short_name="unknown")
    assert ret["result"] is False


def test_no_args():
    ret = st.policy("esx-1")
    assert ret["result"] is False
