"""Tests for the vim_host_config state module."""

import pytest

from saltext.vmware.clients import vim_host_config as c
from saltext.vmware.states import vmware_vim_host_config as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


# ---------- ntp ----------


def test_ntp_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "ntp_get",
        lambda o, h, profile=None: {
            "servers": ["time.example.com"],
            "enabled": True,
            "policy": "on",
        },
    )
    ret = st.ntp("esxi-01", servers=["time.example.com"], running=True, policy="on")
    assert ret["changes"] == {}


def test_ntp_replaces_servers(monkeypatch):
    actions = {"set_servers": [], "set_running": [], "set_policy": []}
    monkeypatch.setattr(
        c,
        "ntp_get",
        lambda o, h, profile=None: {
            "servers": ["old.example.com"],
            "enabled": True,
            "policy": "on",
        },
    )
    monkeypatch.setattr(
        c,
        "ntp_set_servers",
        lambda o, h, s, profile=None: actions["set_servers"].append(s),
    )
    monkeypatch.setattr(
        c, "ntp_set_running", lambda o, h, r, profile=None: actions["set_running"].append(r)
    )
    monkeypatch.setattr(
        c, "ntp_set_policy", lambda o, h, p, profile=None: actions["set_policy"].append(p)
    )
    ret = st.ntp("esxi-01", servers=["new.example.com"])
    assert "servers" in ret["changes"]
    assert actions["set_servers"][0] == ["new.example.com"]
    assert actions["set_running"] == []
    assert actions["set_policy"] == []


def test_ntp_full_drift(monkeypatch):
    actions = {"set_servers": [], "set_running": [], "set_policy": []}
    monkeypatch.setattr(
        c,
        "ntp_get",
        lambda o, h, profile=None: {
            "servers": [],
            "enabled": False,
            "policy": "off",
        },
    )
    monkeypatch.setattr(
        c, "ntp_set_servers", lambda o, h, s, profile=None: actions["set_servers"].append(s)
    )
    monkeypatch.setattr(
        c, "ntp_set_running", lambda o, h, r, profile=None: actions["set_running"].append(r)
    )
    monkeypatch.setattr(
        c, "ntp_set_policy", lambda o, h, p, profile=None: actions["set_policy"].append(p)
    )
    ret = st.ntp("esxi-01", servers=["time.example.com"], running=True, policy="on")
    assert {"servers", "running", "policy"}.issubset(ret["changes"].keys())
    assert actions["set_servers"][0] == ["time.example.com"]
    assert actions["set_running"][0] is True
    assert actions["set_policy"][0] == "on"


def test_ntp_test_mode(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", {**opts, "test": True}, raising=False)
    monkeypatch.setattr(
        c,
        "ntp_get",
        lambda o, h, profile=None: {"servers": [], "enabled": False, "policy": "off"},
    )
    ret = st.ntp("esxi-01", running=True)
    assert ret["result"] is None
    assert "would be updated" in ret["comment"]


# ---------- service ----------


def test_service_starts_when_stopped(monkeypatch):
    actions = {"start": [], "stop": [], "policy": []}
    monkeypatch.setattr(
        c,
        "service_list",
        lambda o, h, profile=None: [
            {"key": "TSM-SSH", "running": False, "policy": "off"},
        ],
    )
    monkeypatch.setattr(
        c, "service_start", lambda o, h, sid, profile=None: actions["start"].append(sid)
    )
    monkeypatch.setattr(
        c, "service_stop", lambda o, h, sid, profile=None: actions["stop"].append(sid)
    )
    monkeypatch.setattr(
        c,
        "service_set_policy",
        lambda o, h, sid, pol, profile=None: actions["policy"].append((sid, pol)),
    )
    ret = st.service("TSM-SSH", host="esxi-01", running=True, policy="on")
    assert "running" in ret["changes"]
    assert "policy" in ret["changes"]
    assert actions["start"] == ["TSM-SSH"]
    assert actions["policy"] == [("TSM-SSH", "on")]


def test_service_already_matches(monkeypatch):
    monkeypatch.setattr(
        c,
        "service_list",
        lambda o, h, profile=None: [{"key": "ntpd", "running": True, "policy": "on"}],
    )
    ret = st.service("ntpd", host="esxi-01", running=True, policy="on")
    assert ret["changes"] == {}


def test_service_missing(monkeypatch):
    monkeypatch.setattr(c, "service_list", lambda o, h, profile=None: [])
    ret = st.service("bogus", host="esxi-01", running=True)
    assert ret["result"] is False


# ---------- advanced_setting ----------


def test_advanced_setting_already_matches(monkeypatch):
    monkeypatch.setattr(c, "advanced_get", lambda o, h, key=None, profile=None: 1)
    ret = st.advanced_setting("k", host="esxi-01", value=1)
    assert ret["changes"] == {}


def test_advanced_setting_updates(monkeypatch):
    actions = {"set": []}
    monkeypatch.setattr(c, "advanced_get", lambda o, h, key=None, profile=None: 0)
    monkeypatch.setattr(
        c, "advanced_set", lambda o, h, k, v, profile=None: actions["set"].append((k, v))
    )
    ret = st.advanced_setting("UserVars.SuppressShellWarning", host="esxi-01", value=1)
    assert ret["changes"] == {"value": (0, 1)}
    assert actions["set"] == [("UserVars.SuppressShellWarning", 1)]


def test_advanced_setting_missing_key(monkeypatch):
    def _raise(*args, **kwargs):
        raise LookupError("missing")

    monkeypatch.setattr(c, "advanced_get", _raise)
    ret = st.advanced_setting("k", host="esxi-01", value=1)
    assert ret["result"] is False


# ---------- ad_joined ----------


def test_ad_joined_already(monkeypatch):
    monkeypatch.setattr(
        c, "ad_status", lambda o, h, profile=None: {"joined": True, "domain": "example.com"}
    )
    ret = st.ad_joined("esxi-01", domain="example.com", username="admin", password="secret")
    assert ret["changes"] == {}


def test_ad_joined_transitions(monkeypatch):
    actions = {"joined": []}
    monkeypatch.setattr(
        c, "ad_status", lambda o, h, profile=None: {"joined": False, "domain": None}
    )
    monkeypatch.setattr(
        c,
        "ad_join",
        lambda o, h, dom, u, p, ou_path=None, profile=None: actions["joined"].append((h, dom, u)),
    )
    ret = st.ad_joined("esxi-01", domain="example.com", username="admin", password="secret")
    assert ret["changes"]["domain"] == (None, "example.com")
    assert actions["joined"][0] == ("esxi-01", "example.com", "admin")
