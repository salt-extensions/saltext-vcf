"""Tests for states.vcf_sddc_host."""

import pytest

from saltext.vcf.clients import sddc_host as r
from saltext.vcf.states import vcf_sddc_host as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {"exists": False, "commissioned": [], "decommissioned": []}

    monkeypatch.setattr(
        r,
        "get_or_none",
        lambda opts, name, profile=None: {"id": name} if state["exists"] else None,
    )
    monkeypatch.setattr(
        r,
        "commission",
        lambda opts, spec, profile=None: state["commissioned"].append(spec),
    )
    monkeypatch.setattr(
        r,
        "decommission",
        lambda opts, name, profile=None: state["decommissioned"].append(name),
    )
    return state


def test_commissioned_already(stub):
    stub["exists"] = True
    ret = st.commissioned("h1")
    assert ret["changes"] == {}
    assert "already commissioned" in ret["comment"]


def test_commissioned_creates(stub):
    ret = st.commissioned("h1")
    assert ret["changes"] == {"commissioned": "h1"}
    assert stub["commissioned"] == [[{"hostfqdn": "h1"}]]


def test_commissioned_test_mode(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.commissioned("h1")
    assert ret["result"] is None
    assert stub["commissioned"] == []


def test_decommissioned_already(stub):
    ret = st.decommissioned("h1")
    assert "already decommissioned" in ret["comment"]


def test_decommissioned_deletes(stub):
    stub["exists"] = True
    ret = st.decommissioned("h1")
    assert ret["changes"] == {"decommissioned": "h1"}
    assert stub["decommissioned"] == ["h1"]
