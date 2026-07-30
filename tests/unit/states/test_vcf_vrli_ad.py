"""Tests for states.vcf_vrli_ad."""

import pytest

from saltext.vcf.clients import vrli_ad as c
from saltext.vcf.states import vcf_vrli_ad as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": {"enableAD": False}, "calls": []}
    monkeypatch.setattr(c, "get", lambda o, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "set_",
        lambda o, spec, profile=None: state["calls"].append(("set", spec)),
    )
    monkeypatch.setattr(c, "disable", lambda o, profile=None: state["calls"].append(("disable",)))
    return state


def test_ad_configured_creates_when_disabled(stub):
    ret = st.ad_configured("ad", "corp.example.com", "svc", "p")
    assert ret["result"] is True
    assert stub["calls"] and stub["calls"][0][0] == "set"
    assert ret["changes"]  # something changed


def test_ad_configured_idempotent_on_matching_tri_key(stub):
    stub["current"] = {
        "enableAD": True,
        "domain": "corp.example.com",
        "username": "svc",
        "connType": "STANDARD",
    }
    ret = st.ad_configured("ad", "corp.example.com", "svc", "p")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_ad_configured_force_bypasses_idempotency(stub):
    stub["current"] = {
        "enableAD": True,
        "domain": "corp.example.com",
        "username": "svc",
        "connType": "STANDARD",
    }
    ret = st.ad_configured("ad", "corp.example.com", "svc", "p", force=True)
    assert ret["changes"] == {"password": "rotated"}
    assert stub["calls"]


def test_ad_configured_test_mode(stub, opts):
    opts["test"] = True
    ret = st.ad_configured("ad", "corp.example.com", "svc", "p")
    assert ret["result"] is None
    assert stub["calls"] == []


def test_ad_disabled_noop_when_already_off(stub):
    ret = st.ad_disabled("ad")
    assert ret["changes"] == {}
    assert stub["calls"] == []


def test_ad_disabled_disables(stub):
    stub["current"] = {"enableAD": True}
    ret = st.ad_disabled("ad")
    assert ret["changes"] == {"enableAD": {"old": True, "new": False}}
    assert stub["calls"] == [("disable",)]
