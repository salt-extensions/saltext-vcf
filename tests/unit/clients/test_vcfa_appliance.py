"""Tests for clients.vcfa_appliance."""

import json

import pytest
import responses

from saltext.vcf.clients import vcfa_appliance as app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app_opts(opts):
    """Extend opts with an appliance section on the mgmt plane (host:5480)."""
    opts["pillar"]["saltext.vcf"]["vcfa"]["appliance"] = {
        "username": "root",
        "password": "root-secret",
    }
    return opts


_BASE_URL = f"https://vcfa.test:{app.DEFAULT_MGMT_PORT}/api/v1/system"


# ---------------------------------------------------------------------------
# TLS
# ---------------------------------------------------------------------------


def test_tls_get_uses_mgmt_port_and_basic_auth(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/tls",
        json={"protocols": ["TLSv1.2", "TLSv1.3"], "cipherSuites": ["A"]},
        status=200,
    )
    out = app.tls_get(app_opts)
    assert out["protocols"] == ["TLSv1.2", "TLSv1.3"]
    auth = mocked_responses.calls[-1].request.headers.get("Authorization", "")
    # Basic base64("root:root-secret") == cm9vdDpyb290LXNlY3JldA==
    assert auth.startswith("Basic ")


def test_tls_set_defaults_to_tls12_and_tls13_and_preserves_ciphers(
    app_opts, mocked_responses
):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/tls",
        json={"protocols": ["TLSv1.0"], "cipherSuites": ["EXISTING"]},
        status=200,
    )
    mocked_responses.add(
        responses.PUT,
        f"{_BASE_URL}/tls",
        json={},
        status=200,
    )
    app.tls_set(app_opts)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["protocols"] == ["TLSv1.2", "TLSv1.3"]
    # Existing cipher suites preserved when caller doesn't override.
    assert body["cipherSuites"] == ["EXISTING"]


def test_tls_set_accepts_caller_protocols_and_ciphers(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET, f"{_BASE_URL}/tls", json={"protocols": []}, status=200
    )
    mocked_responses.add(responses.PUT, f"{_BASE_URL}/tls", json={}, status=200)
    app.tls_set(app_opts, protocols=["TLSv1.3"], cipher_suites=["FOO"])
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"protocols": ["TLSv1.3"], "cipherSuites": ["FOO"]}


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def test_services_list_unwraps_content(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/services",
        json={"content": [{"name": "sshd", "enabled": True}]},
        status=200,
    )
    assert app.services_list(app_opts) == [{"name": "sshd", "enabled": True}]


def test_services_list_bare_list(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/services",
        json=[{"name": "ftp", "enabled": False}],
        status=200,
    )
    assert app.services_list(app_opts) == [{"name": "ftp", "enabled": False}]


def test_service_get_finds_by_name(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/services",
        json={"services": [{"name": "ftp", "enabled": True}]},
        status=200,
    )
    assert app.service_get(app_opts, "ftp")["enabled"] is True
    assert app.service_get(app_opts, "missing") is None


def test_service_disable_skips_when_already_disabled(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/services",
        json=[{"name": "ftp", "enabled": False}],
        status=200,
    )
    out = app.service_disable(app_opts, "ftp")
    assert out["enabled"] is False
    # Only one call — the GET — no PATCH issued.
    assert len(mocked_responses.calls) == 1


def test_service_disable_patches_when_enabled(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/services",
        json=[{"name": "ftp", "enabled": True}],
        status=200,
    )
    mocked_responses.add(
        responses.PATCH,
        f"{_BASE_URL}/services/ftp",
        json={"name": "ftp", "enabled": False},
        status=200,
    )
    out = app.service_disable(app_opts, "ftp")
    assert out["enabled"] is False
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}


def test_service_disable_unknown_raises(app_opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{_BASE_URL}/services", json=[], status=200)
    with pytest.raises(ValueError, match="unknown appliance service"):
        app.service_disable(app_opts, "nope")


def test_service_enable_patches_when_disabled(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/services",
        json=[{"name": "sshd", "enabled": False}],
        status=200,
    )
    mocked_responses.add(
        responses.PATCH,
        f"{_BASE_URL}/services/sshd",
        json={"name": "sshd", "enabled": True},
        status=200,
    )
    out = app.service_enable(app_opts, "sshd")
    assert out["enabled"] is True


def test_firewall_list_bare_list(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/firewall",
        json=[{"port": 22, "protocol": "tcp", "allowed": True}],
        status=200,
    )
    assert app.firewall_list(app_opts)[0]["port"] == 22


# ---------------------------------------------------------------------------
# SSH
# ---------------------------------------------------------------------------


def test_ssh_get(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/ssh",
        json={"enabled": True, "rootLogin": True, "adminLogin": False},
        status=200,
    )
    out = app.ssh_get(app_opts)
    assert out["rootLogin"] is True
    assert out["adminLogin"] is False


def test_ssh_set_merges_partial_updates(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/ssh",
        json={"enabled": True, "rootLogin": False, "adminLogin": False},
        status=200,
    )
    mocked_responses.add(responses.PUT, f"{_BASE_URL}/ssh", json={}, status=200)
    app.ssh_set(app_opts, root_enabled=True, admin_enabled=True)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": True, "rootLogin": True, "adminLogin": True}


def test_ssh_set_only_updates_specified(app_opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE_URL}/ssh",
        json={"enabled": False, "rootLogin": False, "adminLogin": False},
        status=200,
    )
    mocked_responses.add(responses.PUT, f"{_BASE_URL}/ssh", json={}, status=200)
    app.ssh_set(app_opts, enabled=True)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["enabled"] is True
    assert body["rootLogin"] is False
    assert body["adminLogin"] is False


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


def test_mgmt_config_falls_back_to_tenant_host_and_password(opts):
    """Without an ``appliance`` block we still get host+password from tenant cfg."""
    cfg = app._mgmt_config(opts)
    assert cfg["host"] == "vcfa.test"
    assert cfg["username"] == "root"  # default when appliance username unset
    assert cfg["port"] == app.DEFAULT_MGMT_PORT


def test_mgmt_config_allows_custom_port_and_user(opts):
    opts["pillar"]["saltext.vcf"]["vcfa"]["appliance"] = {
        "host": "vcfa-mgmt.test",
        "port": 15480,
        "username": "admin",
        "password": "adm-pw",
    }
    cfg = app._mgmt_config(opts)
    assert cfg["host"] == "vcfa-mgmt.test"
    assert cfg["port"] == 15480
    assert cfg["username"] == "admin"
    assert cfg["password"] == "adm-pw"
