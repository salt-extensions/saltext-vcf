"""Tests for clients.fleet_password (VCF Fleet Management password administration)."""

import json

import responses

from saltext.vcf.clients import fleet_password

BASE = "https://sm.test/api/fleet-management/password-management"


def test_list_accounts(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/accounts",
        json=[{"accountKey": "vc-root", "entity": "vcenter"}, {"accountKey": "nsx-admin"}],
        status=200,
    )
    out = fleet_password.list_accounts(opts)
    assert [a["accountKey"] for a in out] == ["vc-root", "nsx-admin"]


def test_get_account(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/accounts/vc-root",
        json={"accountKey": "vc-root", "entity": "vcenter", "username": "root"},
        status=200,
    )
    out = fleet_password.get_account(opts, "vc-root")
    assert out["username"] == "root"


def test_get_account_or_none_404(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{BASE}/accounts/missing", status=404)
    assert fleet_password.get_account_or_none(opts, "missing") is None


def test_get_password(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/accounts/vc-root/password",
        json={"password": "VMware123!VMware123!"},
        status=200,
    )
    out = fleet_password.get_password(opts, "vc-root")
    assert out["password"].startswith("VMware")


def test_set_password(opts, sddc_authed):
    sddc_authed.add(
        responses.PUT,
        f"{BASE}/accounts/vc-root/password",
        json={"accountKey": "vc-root", "status": "ROTATED"},
        status=200,
    )
    out = fleet_password.set_password(opts, "vc-root", "NewPass1!NewPass1!")
    assert out["status"] == "ROTATED"
    body = json.loads(sddc_authed.calls[-1].request.body)
    assert body == {"password": "NewPass1!NewPass1!"}


def test_rotate(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{BASE}/accounts/vc-root/rotate",
        json={"taskId": "task-42", "status": "IN_PROGRESS"},
        status=202,
    )
    out = fleet_password.rotate(opts, "vc-root")
    assert out["taskId"] == "task-42"


def test_history(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{BASE}/accounts/vc-root/history",
        json=[{"rotatedAt": "2026-05-13T00:00:00Z", "rotatedBy": "auto"}],
        status=200,
    )
    out = fleet_password.history(opts, "vc-root")
    assert out[0]["rotatedBy"] == "auto"
