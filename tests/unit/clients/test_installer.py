"""Tests for VCF Installer clients (system, bringup, credentials, logs)."""

import responses

from saltext.vcf.clients import installer_bringup
from saltext.vcf.clients import installer_credentials
from saltext.vcf.clients import installer_logs
from saltext.vcf.clients import installer_system

BASE = "https://installer.test"


# ---------------------------------------------------------------------------
# system
# ---------------------------------------------------------------------------


def test_status(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET, f"{BASE}/v1/system/status", json={"status": "OPERATIONAL"}, status=200
    )
    assert installer_system.status(opts)["status"] == "OPERATIONAL"


def test_version(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/system/version",
        json={"version": "9.0.0.0", "build": "12345"},
        status=200,
    )
    assert installer_system.version(opts)["version"] == "9.0.0.0"


def test_registration(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/system/registration",
        json={"registered": False},
        status=200,
    )
    assert installer_system.registration(opts) == {"registered": False}


def test_registration_or_none_404(opts, vcf_installer_authed):
    vcf_installer_authed.add(responses.GET, f"{BASE}/v1/system/registration", status=404)
    assert installer_system.registration_or_none(opts) is None


def test_dns_and_ntp(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/system/dns-config",
        json={"dnsServers": ["10.0.0.1"]},
        status=200,
    )
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/system/ntp-config",
        json={"ntpServers": ["time.example.com"]},
        status=200,
    )
    assert installer_system.dns_config(opts)["dnsServers"] == ["10.0.0.1"]
    assert installer_system.ntp_config(opts)["ntpServers"] == ["time.example.com"]


def test_update_dns_config(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.PATCH,
        f"{BASE}/v1/system/dns-config",
        json={"dnsServers": ["10.0.0.2"]},
        status=200,
    )
    out = installer_system.update_dns_config(opts, ["10.0.0.2"], search_domains=["example.com"])
    assert out["dnsServers"] == ["10.0.0.2"]
    import json as json_mod

    body = json_mod.loads(vcf_installer_authed.calls[-1].request.body)
    assert body == {"dnsServers": ["10.0.0.2"], "dnsSearchDomains": ["example.com"]}


def test_sddc_manager_or_none_404(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET, f"{BASE}/v1/sddc-manager-system/sddc-manager", status=404
    )
    assert installer_system.sddc_manager_or_none(opts) is None


# ---------------------------------------------------------------------------
# bringup
# ---------------------------------------------------------------------------


def test_validate_returns_id(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.POST,
        f"{BASE}/v1/sddcs/validations",
        json={"id": "val-1", "executionStatus": "IN_PROGRESS"},
        status=200,
    )
    out = installer_bringup.validate(opts, {"any": "spec"})
    assert out["id"] == "val-1"


def test_validation_status(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/validations/val-1",
        json={"id": "val-1", "executionStatus": "COMPLETED", "resultStatus": "SUCCEEDED"},
        status=200,
    )
    out = installer_bringup.validation_status(opts, "val-1")
    assert out["resultStatus"] == "SUCCEEDED"


def test_wait_validation_succeeds(opts, vcf_installer_authed):
    # Two poll cycles: in-progress, then succeeded
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/validations/val-1",
        json={"executionStatus": "IN_PROGRESS"},
        status=200,
    )
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/validations/val-1",
        json={"executionStatus": "COMPLETED", "resultStatus": "SUCCEEDED"},
        status=200,
    )
    out = installer_bringup.wait_validation(opts, "val-1", timeout=30, poll_interval=0)
    assert out["resultStatus"] == "SUCCEEDED"


def test_wait_validation_fails(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/validations/val-1",
        json={"executionStatus": "COMPLETED", "resultStatus": "FAILED", "errors": ["bad spec"]},
        status=200,
    )
    import pytest

    with pytest.raises(RuntimeError, match="FAILED"):
        installer_bringup.wait_validation(opts, "val-1", timeout=5, poll_interval=0)


def test_submit_and_status(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.POST,
        f"{BASE}/v1/sddcs",
        json={"id": "sddc-1", "status": "IN_PROGRESS"},
        status=200,
    )
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/sddc-1",
        json={"id": "sddc-1", "status": "IN_PROGRESS", "currentStage": "DEPLOY_VCENTER"},
        status=200,
    )
    submitted = installer_bringup.submit(opts, {"any": "spec"})
    assert submitted["id"] == "sddc-1"
    assert installer_bringup.status(opts, "sddc-1")["currentStage"] == "DEPLOY_VCENTER"


def test_wait_succeeds(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/sddc-1",
        json={"status": "IN_PROGRESS"},
        status=200,
    )
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs/sddc-1",
        json={"status": "COMPLETED_WITH_SUCCESS"},
        status=200,
    )
    out = installer_bringup.wait(opts, "sddc-1", timeout=30, poll_interval=0)
    assert out["status"] == "COMPLETED_WITH_SUCCESS"


def test_retry(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.PATCH,
        f"{BASE}/v1/sddcs/sddc-1",
        json={"id": "sddc-1", "status": "IN_PROGRESS"},
        status=200,
    )
    out = installer_bringup.retry(opts, "sddc-1")
    assert out["status"] == "IN_PROGRESS"
    import json as json_mod

    body = json_mod.loads(vcf_installer_authed.calls[-1].request.body)
    assert body == {"action": "RETRY"}


def test_list(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/sddcs",
        json=[{"id": "sddc-1"}, {"id": "sddc-2"}],
        status=200,
    )
    out = installer_bringup.list_(opts)
    assert {t["id"] for t in out} == {"sddc-1", "sddc-2"}


# ---------------------------------------------------------------------------
# credentials
# ---------------------------------------------------------------------------


def test_credentials_list(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/system/security/passwords",
        json=[{"id": "p-1", "username": "root", "entity": "vcenter"}],
        status=200,
    )
    out = installer_credentials.list_(opts)
    assert out[0]["entity"] == "vcenter"


def test_credentials_rotate(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.PATCH,
        f"{BASE}/v1/system/security/passwords/p-1",
        json={"id": "p-1", "status": "ROTATED"},
        status=200,
    )
    out = installer_credentials.rotate(opts, "p-1", "NewPass!")
    assert out["status"] == "ROTATED"


def test_credentials_get_or_none(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.GET, f"{BASE}/v1/system/security/passwords/missing", status=404
    )
    assert installer_credentials.get_or_none(opts, "missing") is None


# ---------------------------------------------------------------------------
# logs
# ---------------------------------------------------------------------------


def test_logs_generate_and_list(opts, vcf_installer_authed):
    vcf_installer_authed.add(
        responses.POST,
        f"{BASE}/v1/system/log-bundles",
        json={"id": "bundle-1", "status": "IN_PROGRESS"},
        status=202,
    )
    vcf_installer_authed.add(
        responses.GET,
        f"{BASE}/v1/system/log-bundles",
        json=[{"id": "bundle-1", "status": "COMPLETED"}],
        status=200,
    )
    out = installer_logs.generate(opts)
    assert out["id"] == "bundle-1"
    assert installer_logs.list_(opts)[0]["status"] == "COMPLETED"
