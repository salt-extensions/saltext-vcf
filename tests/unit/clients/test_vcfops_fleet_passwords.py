"""Tests for clients.vcfops_fleet_passwords."""

import json
from datetime import datetime
from datetime import timezone
from unittest.mock import patch

import pytest
import responses

from saltext.vcf.clients import vcfops_fleet_passwords as fp

_BASE = "https://ops.test/suite-api/api/fleet-management/password-management"


# ---------------------------------------------------------------------------
# _iso helper
# ---------------------------------------------------------------------------


def test_iso_zero_means_no_expiry():
    assert fp._iso(0) is None


def test_iso_none_means_no_expiry():
    assert fp._iso(None) is None


def test_iso_renders_utc_z_string():
    # 2027-03-06T00:00:00Z in unix ms
    assert fp._iso(1804291200000) == "2027-03-06T00:00:00Z"


# ---------------------------------------------------------------------------
# query_accounts
# ---------------------------------------------------------------------------


def test_query_accounts_sends_filters_and_paging(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json={"vcfPasswordAccounts": [], "pageInfo": {"totalCount": 0}},
        status=200,
    )
    fp.query_accounts(
        opts,
        appliance="VCENTER",
        status="EXPIRING",
        page=2,
        page_size=50,
        sort_by="expiryDate",
        sort_order="ASCENDING",
    )
    last = vcfops_authed.calls[-1].request
    body = json.loads(last.body)
    assert body == {"appliance": "VCENTER", "status": "EXPIRING"}
    assert "page=2" in last.url
    assert "pageSize=50" in last.url
    assert "sortBy=expiryDate" in last.url
    assert "sortOrder=ASCENDING" in last.url


# ---------------------------------------------------------------------------
# list_
# ---------------------------------------------------------------------------


def test_list_returns_accounts_and_total_count(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json={
            "vcfPasswordAccounts": [
                {"passwordAccountKey": "a", "expiryDate": 1804291200000},
                {"passwordAccountKey": "b", "expiryDate": 0},
            ],
            "pageInfo": {"totalCount": 2},
        },
        status=200,
    )
    out = fp.list_(opts)
    assert out["totalCount"] == 2
    assert [a["passwordAccountKey"] for a in out["accounts"]] == ["a", "b"]
    assert out["accounts"][0]["expiryDateIso"] == "2027-03-06T00:00:00Z"
    assert out["accounts"][1]["expiryDateIso"] is None


def test_list_walks_pagination(opts, vcfops_authed):
    page0 = {
        "vcfPasswordAccounts": [{"passwordAccountKey": "a"}, {"passwordAccountKey": "b"}],
        "pageInfo": {"totalCount": 3},
    }
    page1 = {
        "vcfPasswordAccounts": [{"passwordAccountKey": "c"}],
        "pageInfo": {"totalCount": 3},
    }
    vcfops_authed.add(responses.POST, f"{_BASE}/accounts/query", json=page0, status=200)
    vcfops_authed.add(responses.POST, f"{_BASE}/accounts/query", json=page1, status=200)

    out = fp.list_(opts, page_size=2)
    assert out["totalCount"] == 3
    assert [a["passwordAccountKey"] for a in out["accounts"]] == ["a", "b", "c"]


def test_list_stops_on_empty_page_when_total_count_missing(opts, vcfops_authed):
    page0 = {"vcfPasswordAccounts": [{"passwordAccountKey": "a"}], "pageInfo": {}}
    page1 = {"vcfPasswordAccounts": [], "pageInfo": {}}
    vcfops_authed.add(responses.POST, f"{_BASE}/accounts/query", json=page0, status=200)
    vcfops_authed.add(responses.POST, f"{_BASE}/accounts/query", json=page1, status=200)
    out = fp.list_(opts)
    assert [a["passwordAccountKey"] for a in out["accounts"]] == ["a"]


# ---------------------------------------------------------------------------
# get_account
# ---------------------------------------------------------------------------


def test_get_account_returns_match(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json={
            "vcfPasswordAccounts": [
                {"passwordAccountKey": "pak-1", "userName": "root"},
                {"passwordAccountKey": "pak-2", "userName": "admin"},
            ],
            "pageInfo": {"totalCount": 2},
        },
        status=200,
    )
    assert fp.get_account(opts, "pak-2")["userName"] == "admin"


def test_get_account_returns_none_when_missing(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json={"vcfPasswordAccounts": [], "pageInfo": {"totalCount": 0}},
        status=200,
    )
    assert fp.get_account(opts, "missing") is None


# ---------------------------------------------------------------------------
# check_expiry
# ---------------------------------------------------------------------------


def _fixed_now():
    return datetime(2026, 5, 23, tzinfo=timezone.utc)


def _accounts_query_response(accounts):
    return {
        "vcfPasswordAccounts": accounts,
        "pageInfo": {"totalCount": len(accounts)},
    }


def test_check_expiry_categorizes_accounts(opts, vcfops_authed):
    accounts = [
        # ~287 days from 2026-05-23: ok
        {"passwordAccountKey": "ok", "expiryDate": 1804291200000},
        # ~13 days from 2026-05-23: expiring (within 90d default)
        {"passwordAccountKey": "expiring", "expiryDate": 1780659600000},
        # past: expiring (negative daysUntilExpiry)
        {"passwordAccountKey": "expired", "expiryDate": 1777939200000},
        # 0: noExpiry
        {"passwordAccountKey": "never", "expiryDate": 0},
    ]
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json=_accounts_query_response(accounts),
        status=200,
    )
    with patch("saltext.vcf.clients.vcfops_fleet_passwords.datetime") as dt:
        dt.now.return_value = _fixed_now()
        # _iso uses datetime.fromtimestamp; delegate to the real datetime
        dt.fromtimestamp.side_effect = datetime.fromtimestamp
        out = fp.check_expiry(opts, threshold_days=90)

    assert out["totalCount"] == 4
    assert out["expiryThresholdDays"] == 90
    assert [a["passwordAccountKey"] for a in out["ok"]] == ["ok"]
    assert sorted(a["passwordAccountKey"] for a in out["expiring"]) == ["expired", "expiring"]
    assert [a["passwordAccountKey"] for a in out["noExpiry"]] == ["never"]
    assert out["okCount"] == 1
    assert out["expiringCount"] == 2
    assert out["noExpiryCount"] == 1


def test_check_expiry_adds_days_until_expiry(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json=_accounts_query_response([{"passwordAccountKey": "ok", "expiryDate": 1804291200000}]),
        status=200,
    )
    with patch("saltext.vcf.clients.vcfops_fleet_passwords.datetime") as dt:
        dt.now.return_value = _fixed_now()
        dt.fromtimestamp.side_effect = datetime.fromtimestamp
        out = fp.check_expiry(opts, threshold_days=90)
    # 2027-03-06 minus 2026-05-23 = 287 days
    assert out["ok"][0]["daysUntilExpiry"] == pytest.approx(287.0, abs=0.5)


def test_check_expiry_no_expiry_entries_omit_days_until_expiry(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/accounts/query",
        json=_accounts_query_response([{"passwordAccountKey": "never", "expiryDate": 0}]),
        status=200,
    )
    out = fp.check_expiry(opts)
    assert "daysUntilExpiry" not in out["noExpiry"][0]


def test_default_threshold_constant():
    assert fp.DEFAULT_EXPIRY_THRESHOLD_DAYS == 90


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_sends_put(opts, vcfops_authed):
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/accounts/pak-1/password",
        json={"requestId": "req-1", "state": "RUNNING"},
        status=200,
    )
    out = fp.update(opts, "pak-1", "old", "new", username="root")
    assert out == {"requestId": "req-1", "state": "RUNNING"}
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body == {"currentPassword": "old", "newPassword": "new", "userName": "root"}


def test_update_omits_username_when_not_given(opts, vcfops_authed):
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/accounts/pak-1/password",
        json={"requestId": "r"},
        status=200,
    )
    fp.update(opts, "pak-1", "old", "new")
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert "userName" not in body
