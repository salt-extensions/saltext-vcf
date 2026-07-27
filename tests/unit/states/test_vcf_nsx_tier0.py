"""Tests for states.vcf_nsx_tier0."""

import pytest

from saltext.vcf.clients import nsx_tier0 as c
from saltext.vcf.states import vcf_nsx_tier0 as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"bgp": None, "ospf": None, "multicast": None, "calls": []}

    def _get(name, kind):
        return lambda opts, tier0, locale_service="default", profile=None: state[kind]

    def _set(kind):
        def _fn(opts, tier0, enabled, locale_service="default", profile=None, **extra):
            state["calls"].append((kind, tier0, bool(enabled), locale_service))
            state[kind] = {"enabled": bool(enabled)}
            return state[kind]

        return _fn

    monkeypatch.setattr(c, "bgp_get", _get("bgp", "bgp"))
    monkeypatch.setattr(c, "ospf_get", _get("ospf", "ospf"))
    monkeypatch.setattr(c, "multicast_get", _get("multicast", "multicast"))
    monkeypatch.setattr(c, "bgp_set", _set("bgp"))
    monkeypatch.setattr(c, "ospf_set", _set("ospf"))
    monkeypatch.setattr(c, "multicast_set", _set("multicast"))
    return state


def test_bgp_disabled_already(stub):
    stub["bgp"] = {"enabled": False}
    ret = st.bgp_disabled("t0-1")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["calls"] == []
    assert "already disabled" in ret["comment"]


def test_bgp_disabled_disables(stub):
    stub["bgp"] = {"enabled": True}
    ret = st.bgp_disabled("t0-1")
    assert ret["result"] is True
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert stub["calls"] == [("bgp", "t0-1", False, "default")]


def test_bgp_disabled_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["bgp"] = {"enabled": True}
    ret = st.bgp_disabled("t0-1")
    assert ret["result"] is None
    assert stub["calls"] == []
    assert "would be disabled" in ret["comment"]


def test_bgp_enabled_true_enables(stub):
    stub["bgp"] = {"enabled": False}
    ret = st.bgp_enabled("t0-1", enabled=True)
    assert ret["changes"] == {"enabled": {"old": False, "new": True}}
    assert stub["calls"] == [("bgp", "t0-1", True, "default")]


def test_ospf_disabled_already(stub):
    stub["ospf"] = {"enabled": False}
    ret = st.ospf_disabled("t0-1")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_ospf_disabled_disables(stub):
    stub["ospf"] = {"enabled": True}
    ret = st.ospf_disabled("t0-1")
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert stub["calls"] == [("ospf", "t0-1", False, "default")]


def test_ospf_disabled_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["ospf"] = {"enabled": True}
    ret = st.ospf_disabled("t0-1")
    assert ret["result"] is None
    assert stub["calls"] == []


def test_multicast_disabled_already(stub):
    stub["multicast"] = {"enabled": False}
    ret = st.multicast_disabled("t0-1")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_multicast_disabled_disables(stub):
    stub["multicast"] = {"enabled": True}
    ret = st.multicast_disabled("t0-1")
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert stub["calls"] == [("multicast", "t0-1", False, "default")]


def test_multicast_disabled_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["multicast"] = {"enabled": True}
    ret = st.multicast_disabled("t0-1")
    assert ret["result"] is None
    assert stub["calls"] == []


def test_disabled_missing_enabled_field_treated_as_false(stub):
    stub["bgp"] = {}  # no 'enabled' key -> treated as False
    ret = st.bgp_disabled("t0-1")
    assert ret["result"] is True
    assert ret["changes"] == {}


def test_custom_locale_service_propagates(stub):
    stub["multicast"] = {"enabled": True}
    ret = st.multicast_disabled("t0-1", locale_service="edge-ls")
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert stub["calls"] == [("multicast", "t0-1", False, "edge-ls")]
