"""Tests for states.vcf_vcenter_statistics."""

import pytest

from saltext.vcf.clients import vcenter_statistics as c
from saltext.vcf.states import vcf_vcenter_statistics as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


CURRENT = {"enabled": True, "interval_minutes": 5, "save_days": 1, "level": 1}


def test_already_matches(monkeypatch):
    monkeypatch.setattr(c, "interval_get", lambda opts, name, profile=None: dict(CURRENT))
    ret = st.interval("past_day", level=1)
    assert ret["changes"] == {}


def test_updates_changed_field(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "interval_get", lambda opts, name, profile=None: dict(CURRENT))
    monkeypatch.setattr(
        c,
        "interval_set",
        lambda opts, name, enabled=None, interval_minutes=None, save_days=None, level=None, profile=None: calls.append(
            (name, level)
        ),
    )
    ret = st.interval("past_day", level=2)
    assert ret["changes"] == {"level": {"old": 1, "new": 2}}
    assert calls == [("past_day", 2)]


def test_test_mode(monkeypatch):
    monkeypatch.setattr(c, "interval_get", lambda opts, name, profile=None: dict(CURRENT))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.interval("past_day", level=2)
    assert ret["result"] is None


def test_unknown_interval(monkeypatch):
    monkeypatch.setattr(c, "interval_get", lambda opts, name, profile=None: None)
    ret = st.interval("past_decade", level=2)
    assert ret["result"] is False
