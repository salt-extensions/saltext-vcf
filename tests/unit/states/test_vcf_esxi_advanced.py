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
