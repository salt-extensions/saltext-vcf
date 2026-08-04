"""Tests for states.vcf_vcenter_advanced_option."""

import pytest

from saltext.vcf.clients import vcenter_advanced_option as c
from saltext.vcf.states import vcf_vcenter_advanced_option as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_advanced_option_already_matches(monkeypatch):
    monkeypatch.setattr(c, "advanced_get", lambda opts, key=None, profile=None: 1)
    ret = st.advanced_option("config.vpxd.stats.maxQueryMetrics", value=1)
    assert ret["changes"] == {}


def test_advanced_option_updates(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "advanced_get", lambda opts, key=None, profile=None: 0)
    monkeypatch.setattr(
        c,
        "advanced_set",
        lambda opts, key, value, profile=None: calls.append((key, value)),
    )
    ret = st.advanced_option("config.vpxd.stats.maxQueryMetrics", value=1)
    assert ret["changes"] == {"value": {"old": 0, "new": 1}}
    assert calls == [("config.vpxd.stats.maxQueryMetrics", 1)]


def test_advanced_option_creates_when_never_set(monkeypatch):
    """``advanced_get`` returns ``None`` for a key vCenter has never seen; ensure we create it."""
    calls = []
    monkeypatch.setattr(c, "advanced_get", lambda opts, key=None, profile=None: None)
    monkeypatch.setattr(
        c,
        "advanced_set",
        lambda opts, key, value, profile=None: calls.append((key, value)),
    )
    ret = st.advanced_option("k", value=1)
    assert ret["changes"] == {"value": {"old": None, "new": 1}}
    assert calls == [("k", 1)]


def test_advanced_option_test_mode(monkeypatch):
    monkeypatch.setattr(c, "advanced_get", lambda opts, key=None, profile=None: 0)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.advanced_option("k", value=1)
    assert ret["result"] is None
