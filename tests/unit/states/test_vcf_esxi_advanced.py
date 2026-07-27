"""Tests for states.vcf_esxi_advanced."""

import pytest

from saltext.vcf.clients import esxi_advanced as c
from saltext.vcf.states import vcf_esxi_advanced as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": None, "calls": []}

    monkeypatch.setattr(c, "get_or_none", lambda opts, key, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "set_value",
        lambda opts, key, value, profile=None: state["calls"].append((key, value)),
    )
    return state


def test_already_matches(stub):
    stub["current"] = {"value": 512}
    ret = st.setting("Net.TcpipHeapMax", 512)
    assert ret["changes"] == {}


def test_change(stub):
    stub["current"] = {"value": 512}
    ret = st.setting("Net.TcpipHeapMax", 1024)
    assert ret["changes"]["value"] == {"old": 512, "new": 1024}
    assert stub["calls"] == [("Net.TcpipHeapMax", 1024)]


def test_missing(stub):
    stub["current"] = None
    ret = st.setting("BogusKey", 1)
    assert ret["result"] is False


def test_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["current"] = {"value": 0}
    ret = st.setting("Net.TcpipHeapMax", 1024)
    assert ret["result"] is None
    assert stub["calls"] == []


# ---------------------------------------------------------------------------
# tps_disabled -- 912 Controls #30 named wrapper
# ---------------------------------------------------------------------------


@pytest.fixture
def tps_stub(monkeypatch):
    """Configurable per-key state for the TPS pair."""
    state = {"values": {}, "calls": []}

    def _get(opts, key, profile=None):
        if key not in state["values"]:
            return None
        return {"value": state["values"][key]}

    def _set(opts, key, value, profile=None):
        state["calls"].append((key, value))
        state["values"][key] = value

    monkeypatch.setattr(c, "get_or_none", _get)
    monkeypatch.setattr(c, "set_value", _set)
    return state


def test_tps_disabled_idempotent(tps_stub):
    tps_stub["values"] = {"Mem.ShareForceSalting": 2, "Mem.ShareScanGHz": 0}
    ret = st.tps_disabled("harden-tps", host="esx-1")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert tps_stub["calls"] == []


def test_tps_disabled_writes_both(tps_stub):
    tps_stub["values"] = {"Mem.ShareForceSalting": 1, "Mem.ShareScanGHz": 4}
    ret = st.tps_disabled("harden-tps", host="esx-1")
    assert ret["result"] is True
    assert ret["changes"]["Mem.ShareForceSalting"] == {"old": 1, "new": 2}
    assert ret["changes"]["Mem.ShareScanGHz"] == {"old": 4, "new": 0}
    assert set(tps_stub["calls"]) == {("Mem.ShareForceSalting", 2), ("Mem.ShareScanGHz", 0)}


def test_tps_disabled_partial_drift(tps_stub):
    tps_stub["values"] = {"Mem.ShareForceSalting": 2, "Mem.ShareScanGHz": 4}
    ret = st.tps_disabled("harden-tps", host="esx-1")
    assert list(ret["changes"]) == ["Mem.ShareScanGHz"]
    assert tps_stub["calls"] == [("Mem.ShareScanGHz", 0)]


def test_tps_disabled_string_value_coerced(tps_stub):
    """Some ESXi builds return numeric advanced settings as strings; still compare equal."""
    tps_stub["values"] = {"Mem.ShareForceSalting": "2", "Mem.ShareScanGHz": "0"}
    ret = st.tps_disabled("harden-tps", host="esx-1")
    assert ret["changes"] == {}


def test_tps_disabled_missing_setting(tps_stub):
    tps_stub["values"] = {"Mem.ShareForceSalting": 2}  # ShareScanGHz absent
    ret = st.tps_disabled("harden-tps", host="esx-1")
    assert ret["result"] is False
    assert "Mem.ShareScanGHz" in ret["comment"]


def test_tps_disabled_test_mode(monkeypatch, tps_stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    tps_stub["values"] = {"Mem.ShareForceSalting": 1, "Mem.ShareScanGHz": 4}
    ret = st.tps_disabled("harden-tps", host="esx-1")
    assert ret["result"] is None
    assert tps_stub["calls"] == []
    assert set(ret["changes"]) == {"Mem.ShareForceSalting", "Mem.ShareScanGHz"}
