"""Tests for clients.fleet_password (VCF Fleet credentials via SDDC Manager)."""

import json

import responses

from saltext.vcf.clients import fleet_password

BASE = "https://sm.test/v1/credentials"


def test_list_accounts(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        BASE,
        json=[{"id": "vc-root", "accountType": "USER"}, {"id": "nsx-admin"}],
        status=200,
    )
    out = fleet_password.list_accounts(opts)
    assert [a["id"] for a in out] == ["vc-root", "nsx-admin"]


def test_get_account(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/vc-root",
        json={"id": "vc-root", "accountType": "USER", "username": "root"},
        status=200,
    )
    out = fleet_password.get_account(opts, "vc-root")
    assert out["username"] == "root"


def test_get_account_or_none_404(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{BASE}/missing", status=404)
    assert fleet_password.get_account_or_none(opts, "missing") is None


def test_get_password(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/vc-root",
        json={"id": "vc-root", "username": "root", "password": "VMware123!VMware123!"},
        status=200,
    )
    out = fleet_password.get_password(opts, "vc-root")
    assert out["password"].startswith("VMware")


def test_set_password(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{BASE}/operations",
        json={"id": "task-42", "status": "IN_PROGRESS"},
        status=202,
    )
    out = fleet_password.set_password(opts, "vc-root", "NewPass1!NewPass1!")
    assert out["id"] == "task-42"
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body["operationType"] == "UPDATE"
    creds = body["elements"][0]["resourceCredentials"][0]
    assert creds["credentialId"] == "vc-root"
    assert creds["password"] == "NewPass1!NewPass1!"


def test_rotate(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{BASE}/operations",
        json={"id": "task-43", "status": "IN_PROGRESS"},
        status=202,
    )
    out = fleet_password.rotate(opts, "vc-root")
    assert out["id"] == "task-43"
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body["operationType"] == "ROTATE"


def test_history(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/vc-root/password-history",
        json=[{"rotatedAt": "2026-05-13T00:00:00Z", "rotatedBy": "auto"}],
        status=200,
    )
    out = fleet_password.history(opts, "vc-root")
    assert out[0]["rotatedBy"] == "auto"
