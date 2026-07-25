"""Tests for states.vcf_nsx_telemetry."""

import pytest

from saltext.vcf.clients import nsx_telemetry as c
from saltext.vcf.states import vcf_nsx_telemetry as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"current": {"optin": True}, "set": []}

    monkeypatch.setattr(c, "get", lambda opts, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "set_optin",
        lambda opts, optin, profile=None: state["set"].append(optin),
    )
    return state


def test_optin_set_no_change_when_already_matches(stub):
    stub["current"] = {"optin": False}
    ret = st.optin_set("nsx-ceip", optin=False)
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["set"] == []


def test_optin_set_flips_true_to_false(stub):
    stub["current"] = {"optin": True}
    ret = st.optin_set("nsx-ceip", optin=False)
    assert ret["result"] is True
    assert ret["changes"] == {"optin": {"old": True, "new": False}}
    assert stub["set"] == [False]


def test_optin_set_flips_false_to_true(stub):
    stub["current"] = {"optin": False}
    ret = st.optin_set("nsx-ceip", optin=True)
    assert ret["changes"] == {"optin": {"old": False, "new": True}}
    assert stub["set"] == [True]


def test_optin_set_test_mode(monkeypatch, stub, opts):
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.optin_set("nsx-ceip", optin=False)
    assert ret["result"] is None
    assert "would change" in ret["comment"]
    assert stub["set"] == []


def test_ceip_disabled_alias_calls_optin_false(stub):
    stub["current"] = {"optin": True}
    ret = st.ceip_disabled("nsx-ceip")
    assert ret["changes"] == {"optin": {"old": True, "new": False}}
    assert stub["set"] == [False]
