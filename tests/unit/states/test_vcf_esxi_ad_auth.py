"""Tests for states.vcf_esxi_ad_auth."""

import pytest

from saltext.vcf.clients import esxi_ad_auth as client
from saltext.vcf.states import vcf_esxi_ad_auth as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def stub(monkeypatch):
    state = {
        "current": {
            "joined": False,
            "domain": None,
            "trusted_domains": [],
            "membership_status": None,
            "smb_file_shares": None,
        },
        "join_calls": [],
        "leave_calls": [],
    }

    def _get(opts, host, profile=None):
        return dict(state["current"])

    def _join(opts, host, domain, username, password, profile=None):
        state["join_calls"].append((host, domain, username, password))
        state["current"].update({"joined": True, "domain": domain})
        return "task-join-1"

    def _leave(opts, host, force=False, profile=None):
        state["leave_calls"].append((host, force))
        state["current"].update({"joined": False, "domain": None})
        return "task-leave-1"

    monkeypatch.setattr(client, "get_ad_state", _get)
    monkeypatch.setattr(client, "join_domain", _join)
    monkeypatch.setattr(client, "leave_domain", _leave)
    return state


# ---------------- joined ----------------


def test_joined_no_op_when_already_joined_same_domain(stub):
    stub["current"].update({"joined": True, "domain": "corp.example.com"})
    ret = st.joined("esxi-01", domain="corp.example.com", username="u", password="p")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["join_calls"] == []


def test_joined_case_insensitive_match(stub):
    stub["current"].update({"joined": True, "domain": "CORP.EXAMPLE.COM"})
    ret = st.joined("esxi-01", domain="corp.example.com", username="u", password="p")
    assert ret["changes"] == {}
    assert stub["join_calls"] == []


def test_joined_refuses_switch_between_domains(stub):
    stub["current"].update({"joined": True, "domain": "other.example.com"})
    ret = st.joined("esxi-01", domain="corp.example.com", username="u", password="p")
    assert ret["result"] is False
    assert stub["join_calls"] == []
    assert "left first" in ret["comment"]


def test_joined_performs_join(stub):
    ret = st.joined("esxi-01", domain="corp.example.com", username="u", password="p")
    assert ret["result"] is True
    assert stub["join_calls"] == [("esxi-01", "corp.example.com", "u", "p")]
    assert ret["changes"]["task"] == "task-join-1"
    assert ret["changes"]["joined"] == {"old": None, "new": "corp.example.com"}


def test_joined_test_mode_makes_no_calls(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.joined("esxi-01", domain="corp.example.com", username="u", password="p")
    assert ret["result"] is None
    assert stub["join_calls"] == []


def test_joined_honors_host_kw(stub):
    ret = st.joined(
        "some-state-id",
        domain="corp.example.com",
        username="u",
        password="p",
        host="esxi-42",
    )
    assert ret["result"] is True
    assert stub["join_calls"] == [("esxi-42", "corp.example.com", "u", "p")]


# ---------------- left ----------------


def test_left_no_op_when_not_joined(stub):
    ret = st.left("esxi-01")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert stub["leave_calls"] == []


def test_left_performs_leave(stub):
    stub["current"].update({"joined": True, "domain": "corp.example.com"})
    ret = st.left("esxi-01", force=True)
    assert ret["result"] is True
    assert stub["leave_calls"] == [("esxi-01", True)]
    assert ret["changes"]["joined"] == {"old": "corp.example.com", "new": None}


def test_left_test_mode_makes_no_calls(monkeypatch, stub):
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    stub["current"].update({"joined": True, "domain": "corp.example.com"})
    ret = st.left("esxi-01")
    assert ret["result"] is None
    assert stub["leave_calls"] == []
