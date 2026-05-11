"""Tests for the NSX DFW state modules."""

import pytest

from saltext.vmware.clients import nsx_firewall_rule as c_rule
from saltext.vmware.clients import nsx_security_policy as c_sp
from saltext.vmware.clients import nsx_service as c_svc
from saltext.vmware.states import vmware_nsx_firewall_rule as st_rule
from saltext.vmware.states import vmware_nsx_security_policy as st_sp
from saltext.vmware.states import vmware_nsx_service as st_svc


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (st_sp, st_rule, st_svc):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


@pytest.fixture
def stub_sp(monkeypatch):
    state = {"exists": False, "created": [], "deleted": []}
    monkeypatch.setattr(
        c_sp,
        "get_or_none",
        lambda opts, name, domain="default", profile=None: (
            {"id": name} if state["exists"] else None
        ),
    )
    monkeypatch.setattr(
        c_sp,
        "create",
        lambda opts, name, domain="default", profile=None, **k: state["created"].append((name, k)),
    )
    monkeypatch.setattr(
        c_sp,
        "delete",
        lambda opts, name, domain="default", profile=None: state["deleted"].append(name),
    )
    return state


@pytest.fixture
def stub_rule(monkeypatch):
    state = {"exists": False, "created": [], "deleted": []}
    monkeypatch.setattr(
        c_rule,
        "get_or_none",
        lambda opts, rule, policy, domain="default", profile=None: (
            {"id": rule} if state["exists"] else None
        ),
    )
    monkeypatch.setattr(
        c_rule,
        "create",
        lambda opts, rule, policy, domain="default", profile=None, **k: state["created"].append(
            (rule, policy, k)
        ),
    )
    monkeypatch.setattr(
        c_rule,
        "delete",
        lambda opts, rule, policy, domain="default", profile=None: state["deleted"].append(
            (rule, policy)
        ),
    )
    return state


@pytest.fixture
def stub_svc(monkeypatch):
    state = {"exists": False, "created": [], "deleted": []}
    monkeypatch.setattr(
        c_svc,
        "get_or_none",
        lambda opts, svc, profile=None: {"id": svc} if state["exists"] else None,
    )
    monkeypatch.setattr(
        c_svc,
        "create",
        lambda opts, svc, profile=None, **k: state["created"].append((svc, k)),
    )
    monkeypatch.setattr(
        c_svc,
        "delete",
        lambda opts, svc, profile=None: state["deleted"].append(svc),
    )
    return state


def test_sp_present_creates(stub_sp):
    ret = st_sp.present("sp-a", category="Application")
    assert ret["changes"] == {"new": "sp-a"}
    assert stub_sp["created"][0][0] == "sp-a"


def test_sp_present_idempotent(stub_sp):
    stub_sp["exists"] = True
    ret = st_sp.present("sp-a")
    assert ret["changes"] == {}


def test_sp_absent_deletes(stub_sp):
    stub_sp["exists"] = True
    ret = st_sp.absent("sp-a")
    assert ret["changes"] == {"deleted": "sp-a"}


def test_rule_present_creates(stub_rule):
    ret = st_rule.present("r1", "sp-a", action="ALLOW")
    assert ret["changes"] == {"new": "r1"}
    assert stub_rule["created"][0][:2] == ("r1", "sp-a")
    assert stub_rule["created"][0][2]["action"] == "ALLOW"


def test_rule_test_mode(monkeypatch, stub_rule):
    monkeypatch.setattr(st_rule, "__opts__", {"test": True}, raising=False)
    ret = st_rule.present("r1", "sp-a")
    assert ret["result"] is None
    assert stub_rule["created"] == []


def test_svc_present_creates(stub_svc):
    ret = st_svc.present("MYSVC", service_entries=[])
    assert ret["changes"] == {"new": "MYSVC"}
