"""Tests for states.vcf_vcfa_appliance."""

import pytest

from saltext.vcf.clients import vcfa_appliance as c
from saltext.vcf.states import vcf_vcfa_appliance as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


@pytest.fixture
def tls_stub(monkeypatch):
    state = {"current": {"protocols": ["TLSv1.2", "TLSv1.3"]}, "set": []}

    monkeypatch.setattr(c, "tls_get", lambda opts, profile=None: state["current"])

    def set_tls(opts, protocols=None, cipher_suites=None, profile=None):
        state["set"].append({"protocols": protocols, "cipher_suites": cipher_suites})
        return {}

    monkeypatch.setattr(c, "tls_set", set_tls)
    return state


@pytest.fixture
def svc_stub(monkeypatch):
    state = {"services": {}, "set": []}

    monkeypatch.setattr(
        c,
        "service_get",
        lambda opts, name, profile=None: state["services"].get(name),
    )

    def set_enabled(opts, name, enabled, profile=None):
        state["set"].append((name, enabled))
        return {"name": name, "enabled": enabled}

    monkeypatch.setattr(c, "service_set_enabled", set_enabled)
    return state


@pytest.fixture
def ssh_stub(monkeypatch):
    state = {"current": {"enabled": True, "rootLogin": True, "adminLogin": True}, "set": []}

    monkeypatch.setattr(c, "ssh_get", lambda opts, profile=None: state["current"])

    def set_ssh(opts, enabled=None, root_enabled=None, admin_enabled=None, profile=None):
        state["set"].append(
            {"enabled": enabled, "root_enabled": root_enabled, "admin_enabled": admin_enabled}
        )
        return {}

    monkeypatch.setattr(c, "ssh_set", set_ssh)
    return state


# -- TLS -------------------------------------------------------------------


def test_tls_configured_no_change(tls_stub):
    tls_stub["current"] = {"protocols": ["TLSv1.2", "TLSv1.3"]}
    ret = st.tls_configured("tls")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert tls_stub["set"] == []


def test_tls_configured_default_pins_12_and_13(tls_stub):
    tls_stub["current"] = {"protocols": ["TLSv1.0", "TLSv1.1"]}
    ret = st.tls_configured("tls")
    assert ret["result"] is True
    assert "protocols" in ret["changes"]
    assert ret["changes"]["protocols"]["new"] == ["TLSv1.2", "TLSv1.3"]
    assert tls_stub["set"] == [
        {"protocols": ["TLSv1.2", "TLSv1.3"], "cipher_suites": None}
    ]


def test_tls_configured_test_mode(tls_stub, opts, monkeypatch):
    tls_stub["current"] = {"protocols": ["TLSv1.0"]}
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.tls_configured("tls")
    assert ret["result"] is None
    assert "would be updated" in ret["comment"]
    assert tls_stub["set"] == []


def test_tls_configured_detects_cipher_drift(tls_stub):
    tls_stub["current"] = {
        "protocols": ["TLSv1.2", "TLSv1.3"],
        "cipherSuites": ["OLD"],
    }
    ret = st.tls_configured("tls", cipher_suites=["NEW"])
    assert ret["result"] is True
    assert "cipherSuites" in ret["changes"]
    assert tls_stub["set"][-1]["cipher_suites"] == ["NEW"]


def test_tls_configured_accepts_order_insensitive_match(tls_stub):
    tls_stub["current"] = {"protocols": ["TLSv1.3", "TLSv1.2"]}
    ret = st.tls_configured("tls")
    assert ret["changes"] == {}
    assert tls_stub["set"] == []


# -- service_disabled ------------------------------------------------------


def test_service_disabled_no_change_when_already_off(svc_stub):
    svc_stub["services"]["ftp"] = {"name": "ftp", "enabled": False}
    ret = st.service_disabled("ftp")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert svc_stub["set"] == []


def test_service_disabled_flips_enabled_to_disabled(svc_stub):
    svc_stub["services"]["ftp"] = {"name": "ftp", "enabled": True}
    ret = st.service_disabled("ftp")
    assert ret["result"] is True
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert svc_stub["set"] == [("ftp", False)]


def test_service_disabled_unknown_service_returns_failure(svc_stub):
    ret = st.service_disabled("bogus")
    assert ret["result"] is False
    assert "unknown" in ret["comment"]
    assert svc_stub["set"] == []


def test_service_disabled_test_mode(svc_stub, opts, monkeypatch):
    svc_stub["services"]["ftp"] = {"name": "ftp", "enabled": True}
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.service_disabled("ftp")
    assert ret["result"] is None
    assert "would be disabled" in ret["comment"]
    assert svc_stub["set"] == []


def test_service_disabled_uses_explicit_service_arg(svc_stub):
    svc_stub["services"]["telnet"] = {"name": "telnet", "enabled": True}
    ret = st.service_disabled("close-telnet-912", service="telnet")
    assert ret["changes"] == {"enabled": {"old": True, "new": False}}
    assert svc_stub["set"] == [("telnet", False)]


def test_service_enabled_flips_off_to_on(svc_stub):
    svc_stub["services"]["sshd"] = {"name": "sshd", "enabled": False}
    ret = st.service_enabled("sshd")
    assert ret["changes"] == {"enabled": {"old": False, "new": True}}
    assert svc_stub["set"] == [("sshd", True)]


# -- ssh_configured --------------------------------------------------------


def test_ssh_configured_no_change_when_matches_defaults(ssh_stub):
    ssh_stub["current"] = {"enabled": True, "rootLogin": True, "adminLogin": True}
    ret = st.ssh_configured("ssh")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert ssh_stub["set"] == []


def test_ssh_configured_enables_root_when_missing(ssh_stub):
    ssh_stub["current"] = {"enabled": True, "rootLogin": False, "adminLogin": True}
    ret = st.ssh_configured("ssh")
    assert ret["result"] is True
    assert ret["changes"] == {"rootLogin": {"old": False, "new": True}}
    assert ssh_stub["set"] == [
        {"enabled": True, "root_enabled": True, "admin_enabled": True}
    ]


def test_ssh_configured_disables_when_requested(ssh_stub):
    ssh_stub["current"] = {"enabled": True, "rootLogin": True, "adminLogin": True}
    ret = st.ssh_configured("ssh", enabled=False, root_enabled=False, admin_enabled=False)
    assert set(ret["changes"].keys()) == {"enabled", "rootLogin", "adminLogin"}
    assert ssh_stub["set"] == [
        {"enabled": False, "root_enabled": False, "admin_enabled": False}
    ]


def test_ssh_configured_test_mode(ssh_stub, opts, monkeypatch):
    ssh_stub["current"] = {"enabled": False, "rootLogin": False, "adminLogin": False}
    opts["test"] = True
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    ret = st.ssh_configured("ssh")
    assert ret["result"] is None
    assert "would be updated" in ret["comment"]
    assert ssh_stub["set"] == []
