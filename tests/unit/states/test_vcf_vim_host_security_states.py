"""Tests for the vcf_vim_host_security state module (users, password, lockdown)."""

import pytest

from saltext.vcf.clients import vim_host_security as c
from saltext.vcf.states import vcf_vim_host_security as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


# ---------- user_present ----------


def test_user_present_creates(monkeypatch):
    monkeypatch.setattr(c, "user_get_or_none", lambda o, h, u, profile=None: None)
    called = {}
    monkeypatch.setattr(c, "user_create", lambda o, h, u, p, **kw: called.update(user=u, pw=p, **kw))
    ret = st.user_present("svc-audit", "esxi-01", password="pw", description="audit")
    assert ret["changes"] == {"new": "svc-audit"}
    assert called == {"user": "svc-audit", "pw": "pw", "description": "audit", "profile": None}


def test_user_present_updates_on_drift(monkeypatch):
    monkeypatch.setattr(
        c,
        "user_get_or_none",
        lambda o, h, u, profile=None: {"principal": u, "full_name": "old", "group": False},
    )
    calls = []
    monkeypatch.setattr(c, "user_update", lambda o, h, u, **kw: calls.append((u, kw)))
    ret = st.user_present("svc-audit", "esxi-01", password="newpw", description="new desc")
    assert ret["result"] is True
    assert ret["changes"]["description"] == ("old", "new desc")
    assert calls[0][0] == "svc-audit"


def test_user_present_noop_when_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "user_get_or_none",
        lambda o, h, u, profile=None: {"principal": u, "full_name": "Salt User", "group": False},
    )
    ret = st.user_present("svc-audit", "esxi-01")
    assert ret["changes"] == {}


def test_user_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "user_get_or_none", lambda o, h, u, profile=None: None)
    monkeypatch.setattr(c, "user_create", lambda *a, **kw: pytest.fail("must not create"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.user_present("svc-audit", "esxi-01", password="pw")
    assert ret["result"] is None
    assert ret["changes"] == {"new": "svc-audit"}


# ---------- user_absent ----------


def test_user_absent_removes(monkeypatch):
    monkeypatch.setattr(
        c, "user_get_or_none", lambda o, h, u, profile=None: {"principal": u, "full_name": None}
    )
    monkeypatch.setattr(c, "user_delete", lambda o, h, u, profile=None: None)
    ret = st.user_absent("svc-audit", "esxi-01")
    assert ret["changes"] == {"old": "svc-audit"}


def test_user_absent_noop(monkeypatch):
    monkeypatch.setattr(c, "user_get_or_none", lambda o, h, u, profile=None: None)
    ret = st.user_absent("svc-audit", "esxi-01")
    assert ret["changes"] == {}


# ---------- password_present ----------


def test_password_present_updates(monkeypatch):
    monkeypatch.setattr(
        c, "user_update", lambda o, h, u, password=None, description=None, profile=None: None
    )
    ret = st.password_present("root", "esxi-01", "NewSecret!")
    assert ret["result"] is True
    assert ret["changes"] == {"password": ("(existing)", "(new)")}


def test_password_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "user_update", lambda *a, **kw: pytest.fail("must not update"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.password_present("root", "esxi-01", "NewSecret!")
    assert ret["result"] is None


# ---------- lockdown ----------


def test_lockdown_enable_with_exceptions(monkeypatch):
    monkeypatch.setattr(
        c, "lockdown_get", lambda o, h, profile=None: {"mode": "lockdownDisabled", "exception_users": []}
    )
    calls = []
    monkeypatch.setattr(c, "lockdown_set", lambda o, h, m, profile=None: calls.append(("mode", m)))
    monkeypatch.setattr(
        c, "lockdown_set_exception_users", lambda o, h, u, profile=None: calls.append(("users", u))
    )
    ret = st.lockdown("ld", "esxi-01", True, exception_users=["salt-user"])
    assert ret["changes"]["mode"] == ("lockdownDisabled", "lockdownNormal")
    assert ("mode", "lockdownNormal") in calls
    assert ("users", ["salt-user"]) in calls


def test_lockdown_noop(monkeypatch):
    monkeypatch.setattr(
        c,
        "lockdown_get",
        lambda o, h, profile=None: {"mode": "lockdownNormal", "exception_users": ["salt-user"]},
    )
    ret = st.lockdown("ld", "esxi-01", True, exception_users=["salt-user"])
    assert ret["changes"] == {}
