"""Tests for the VCF Installer bringup client.

Note: ``installer_system``, ``installer_credentials`` and ``installer_logs``
modules were removed pending real-endpoint verification — their /v1/system/*
paths did not exist on the live VCF Installer build that was probed. The
bringup endpoints below are also provisional until exercised against a
live installer pod.
"""

import responses

from saltext.vcf.clients import installer_bringup

BASE = "https://installer.test"


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
