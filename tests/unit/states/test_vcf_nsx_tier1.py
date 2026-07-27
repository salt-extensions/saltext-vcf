"""Tests for states.vcf_nsx_tier1."""

import pytest

from saltext.vcf.clients import nsx_tier1 as c
from saltext.vcf.states import vcf_nsx_tier1 as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"multicast": None, "calls": []}

    def _get(opts, tier1, locale_service="default", profile=None):
        return state["multicast"]

    def _set(opts, tier1, enabled, locale_service="default", profile=None, **extra):
        state["calls"].append((tier1, bool(enabled), locale_service))
        state["multicast"] = {"enabled": bool(enabled)}
        return state["multicast"]

    monkeypatch.setattr(c, "multicast_get", _get)
    monkeypatch.setattr(c, "multicast_set", _set)
    return state


def test_multicast_disabled_already(stub):
    stub["multicast"] = {"enabled": False}
    ret = st.multicast_disabled("t1-a")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["calls"] == []
    assert "already disabled" in ret["comment"]


def test_multicast_disabled_disables(stub):
    stub["multicast"] = {"enabled": True}
    ret = st.multicast_disabled("t1-a")
    assert ret["result"] is True
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert stub["calls"] == [("t1-a", False, "default")]


def test_multicast_disabled_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["multicast"] = {"enabled": True}
    ret = st.multicast_disabled("t1-a")
    assert ret["result"] is None
    assert stub["calls"] == []
    assert "would be disabled" in ret["comment"]


def test_multicast_enabled_true(stub):
    stub["multicast"] = {"enabled": False}
    ret = st.multicast_enabled("t1-a", enabled=True)
    assert ret["changes"] == {"enabled": {"old": False, "new": True}}
    assert stub["calls"] == [("t1-a", True, "default")]


def test_multicast_disabled_custom_locale_service(stub):
    stub["multicast"] = {"enabled": True}
    ret = st.multicast_disabled("t1-a", locale_service="ls-alt")
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert stub["calls"] == [("t1-a", False, "ls-alt")]


def test_multicast_disabled_missing_enabled_field(stub):
    stub["multicast"] = {}
    ret = st.multicast_disabled("t1-a")
    assert ret["result"] is True
    assert ret["changes"] == {}
