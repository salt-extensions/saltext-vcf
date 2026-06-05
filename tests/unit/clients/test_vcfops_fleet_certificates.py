"""Tests for clients.vcfops_fleet_certificates."""

import json
from datetime import datetime
from datetime import timezone
from unittest.mock import patch

import pytest
import responses

from saltext.vcf.clients import vcfops_fleet_certificates as fc

_BASE = "https://ops.test/suite-api/api/fleet-management/certificate-management"


# ---------------------------------------------------------------------------
# _iso helper
# ---------------------------------------------------------------------------


def test_iso_zero_means_no_expiry():
    assert fc._iso(0) is None


def test_iso_none_means_no_expiry():
    assert fc._iso(None) is None


def test_iso_renders_utc_z_string():
    # 2027-03-06T00:00:00Z in unix ms
    assert fc._iso(1804291200000) == "2027-03-06T00:00:00Z"


# ---------------------------------------------------------------------------
# query_certificates
# ---------------------------------------------------------------------------


def test_query_certificates_sends_filters_and_paging(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json={"vcfCertificateModels": [], "pageInfo": {"totalCount": 0}},
        status=200,
    )
    fc.query_certificates(
        opts,
        appliance="VCENTER",
        appliance_fqdn="vc01.example.com",
        status="EXPIRING",
        category="TLS_CERT",
        page=1,
        page_size=50,
    )
    last = vcfops_authed.calls[-1].request
    body = json.loads(last.body)
    assert body == {
        "appliance": "VCENTER",
        "applianceFqdn": "vc01.example.com",
        "status": "EXPIRING",
        "category": "TLS_CERT",
    }
    assert "page=1" in last.url
    assert "pageSize=50" in last.url


def test_query_certificates_omits_unset_filters(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json={"vcfCertificateModels": [], "pageInfo": {"totalCount": 0}},
        status=200,
    )
    fc.query_certificates(opts, appliance="NSX")
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body == {"appliance": "NSX"}
    assert "applianceFqdn" not in body
    assert "status" not in body
    assert "category" not in body


# ---------------------------------------------------------------------------
# list_
# ---------------------------------------------------------------------------


def test_list_returns_certificates_and_total_count(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json={
            "vcfCertificateModels": [
                {
                    "certificateResourceKey": "uuid-1",
                    "appliance": "VCENTER",
                    "expiryDate": 1804291200000,
                },
                {
                    "certificateResourceKey": "uuid-2",
                    "appliance": "NSX",
                    "expiryDate": 0,
                },
            ],
            "pageInfo": {"totalCount": 2},
        },
        status=200,
    )
    out = fc.list_(opts)
    assert out["totalCount"] == 2
    assert [c["certificateResourceKey"] for c in out["certificates"]] == ["uuid-1", "uuid-2"]
    assert out["certificates"][0]["expiryDateIso"] == "2027-03-06T00:00:00Z"
    assert out["certificates"][1]["expiryDateIso"] is None


def test_list_walks_pagination(opts, vcfops_authed):
    page0 = {
        "vcfCertificateModels": [
            {"certificateResourceKey": "a"},
            {"certificateResourceKey": "b"},
        ],
        "pageInfo": {"totalCount": 3},
    }
    page1 = {
        "vcfCertificateModels": [{"certificateResourceKey": "c"}],
        "pageInfo": {"totalCount": 3},
    }
    vcfops_authed.add(responses.POST, f"{_BASE}/certificates/query", json=page0, status=200)
    vcfops_authed.add(responses.POST, f"{_BASE}/certificates/query", json=page1, status=200)

    out = fc.list_(opts, page_size=2)
    assert out["totalCount"] == 3
    assert [c["certificateResourceKey"] for c in out["certificates"]] == ["a", "b", "c"]


def test_list_stops_on_empty_page_when_total_count_missing(opts, vcfops_authed):
    page0 = {"vcfCertificateModels": [{"certificateResourceKey": "a"}], "pageInfo": {}}
    page1 = {"vcfCertificateModels": [], "pageInfo": {}}
    vcfops_authed.add(responses.POST, f"{_BASE}/certificates/query", json=page0, status=200)
    vcfops_authed.add(responses.POST, f"{_BASE}/certificates/query", json=page1, status=200)
    out = fc.list_(opts)
    assert [c["certificateResourceKey"] for c in out["certificates"]] == ["a"]


def test_list_passes_filters_to_query(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json={"vcfCertificateModels": [], "pageInfo": {"totalCount": 0}},
        status=200,
    )
    fc.list_(opts, appliance="VCENTER", status="NORMAL", category="TLS_CERT")
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body["appliance"] == "VCENTER"
    assert body["status"] == "NORMAL"
    assert body["category"] == "TLS_CERT"


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_returns_enriched_certificate(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/certificates/uuid-99",
        json={
            "certificateResourceKey": "uuid-99",
            "appliance": "VCENTER",
            "expiryDate": 1804291200000,
        },
        status=200,
    )
    cert = fc.get(opts, "uuid-99")
    assert cert["certificateResourceKey"] == "uuid-99"
    assert cert["expiryDateIso"] == "2027-03-06T00:00:00Z"


def test_get_returns_none_on_empty_response(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/certificates/missing",
        body=b"",
        status=200,
    )
    assert fc.get(opts, "missing") is None


# ---------------------------------------------------------------------------
# check_expiry
# ---------------------------------------------------------------------------


def _fixed_now():
    return datetime(2026, 5, 23, tzinfo=timezone.utc)


def _certs_query_response(certs):
    return {
        "vcfCertificateModels": certs,
        "pageInfo": {"totalCount": len(certs)},
    }


def test_check_expiry_categorizes_certificates(opts, vcfops_authed):
    certs = [
        # ~287 days from 2026-05-23: ok
        {"certificateResourceKey": "ok", "expiryDate": 1804291200000},
        # ~13 days from 2026-05-23: expiring (within 90d default)
        {"certificateResourceKey": "expiring", "expiryDate": 1780659600000},
        # past: expiring (negative daysUntilExpiry)
        {"certificateResourceKey": "expired", "expiryDate": 1777939200000},
        # 0: noExpiry
        {"certificateResourceKey": "never", "expiryDate": 0},
    ]
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json=_certs_query_response(certs),
        status=200,
    )
    with patch("saltext.vcf.clients.vcfops_fleet_certificates.datetime") as dt:
        dt.now.return_value = _fixed_now()
        dt.fromtimestamp.side_effect = datetime.fromtimestamp
        out = fc.check_expiry(opts, threshold_days=90)

    assert out["totalCount"] == 4
    assert out["expiryThresholdDays"] == 90
    assert [c["certificateResourceKey"] for c in out["ok"]] == ["ok"]
    assert sorted(c["certificateResourceKey"] for c in out["expiring"]) == ["expired", "expiring"]
    assert [c["certificateResourceKey"] for c in out["noExpiry"]] == ["never"]
    assert out["okCount"] == 1
    assert out["expiringCount"] == 2
    assert out["noExpiryCount"] == 1


def test_check_expiry_adds_days_until_expiry(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json=_certs_query_response(
            [{"certificateResourceKey": "ok", "expiryDate": 1804291200000}]
        ),
        status=200,
    )
    with patch("saltext.vcf.clients.vcfops_fleet_certificates.datetime") as dt:
        dt.now.return_value = _fixed_now()
        dt.fromtimestamp.side_effect = datetime.fromtimestamp
        out = fc.check_expiry(opts, threshold_days=90)
    # 2027-03-06 minus 2026-05-23 = 287 days
    assert out["ok"][0]["daysUntilExpiry"] == pytest.approx(287.0, abs=0.5)


def test_check_expiry_no_expiry_entries_omit_days_until_expiry(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json=_certs_query_response([{"certificateResourceKey": "never", "expiryDate": 0}]),
        status=200,
    )
    out = fc.check_expiry(opts)
    assert "daysUntilExpiry" not in out["noExpiry"][0]


def test_default_threshold_constant():
    assert fc.DEFAULT_EXPIRY_THRESHOLD_DAYS == 90


def test_check_expiry_passes_filters_to_list(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/certificates/query",
        json=_certs_query_response([]),
        status=200,
    )
    fc.check_expiry(opts, appliance="NSX", appliance_fqdn="nsx01.example.com")
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body["appliance"] == "NSX"
    assert body["applianceFqdn"] == "nsx01.example.com"


# ---------------------------------------------------------------------------
# replace
# ---------------------------------------------------------------------------


def test_replace_external_ca_sends_put_with_chain(opts, vcfops_authed):
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/certificates/uuid-1",
        json={"requestId": "req-1", "state": "INPROGRESS"},
        status=200,
    )
    pem = "-----BEGIN CERTIFICATE-----\nABC\n-----END CERTIFICATE-----\n"
    out = fc.replace(opts, "uuid-1", "EXTERNAL_CA", certificate_chain=pem)
    assert out == {"requestId": "req-1", "state": "INPROGRESS"}
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body == {"caType": "EXTERNAL_CA", "certificateChain": pem}


def test_replace_msca_omits_certificate_chain(opts, vcfops_authed):
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/certificates/uuid-2",
        json={"requestId": "req-2", "state": "INPROGRESS"},
        status=200,
    )
    fc.replace(opts, "uuid-2", "MSCA")
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body == {"caType": "MSCA"}
    assert "certificateChain" not in body


# ---------------------------------------------------------------------------
# list_csrs
# ---------------------------------------------------------------------------


def test_list_csrs_returns_csr_list(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/csrs",
        json={
            "certificateSignatureInfo": [
                {"id": "csr-1", "commonName": "vc01.example.com", "csr": "-----BEGIN..."},
            ],
            "pageInfo": {"totalCount": 1},
        },
        status=200,
    )
    out = fc.list_csrs(opts)
    assert len(out) == 1
    assert out[0]["id"] == "csr-1"


def test_list_csrs_sends_common_name_filter(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/csrs",
        json={"certificateSignatureInfo": []},
        status=200,
    )
    fc.list_csrs(opts, common_name="vc01.example.com")
    assert "commonName=vc01.example.com" in vcfops_authed.calls[-1].request.url


def test_list_csrs_returns_empty_list_on_missing_key(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/csrs",
        json={},
        status=200,
    )
    assert fc.list_csrs(opts) == []


# ---------------------------------------------------------------------------
# generate_csr
# ---------------------------------------------------------------------------


def test_generate_csr_sends_correct_body(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/csrs",
        json={"requestId": "req-csr-1", "state": "INPROGRESS"},
        status=200,
    )
    out = fc.generate_csr(
        opts,
        "uuid-1",
        common_name="vc01.example.com",
        organization="Acme Corp",
        org_unit="IT",
        locality="Amsterdam",
        state="NH",
        country="NL",
        subject_alt_names={"dns": ["vc01.example.com"], "ip": ["10.0.0.1"]},
        email="admin@example.com",
        key_size="KEY_4096",
        key_algorithm="RSA",
    )
    assert out["requestId"] == "req-csr-1"
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body["certificateId"] == "uuid-1"
    spec = body["generateCsrSpec"]
    assert spec["commonName"] == "vc01.example.com"
    assert spec["organization"] == "Acme Corp"
    assert spec["orgUnit"] == "IT"
    assert spec["locality"] == "Amsterdam"
    assert spec["state"] == "NH"
    assert spec["country"] == "NL"
    assert spec["keySize"] == "KEY_4096"
    assert spec["keyAlgorithm"] == "RSA"
    assert spec["email"] == "admin@example.com"
    assert spec["subjectAltNames"] == {"dns": ["vc01.example.com"], "ip": ["10.0.0.1"]}


def test_generate_csr_omits_optional_fields_when_not_given(opts, vcfops_authed):
    vcfops_authed.add(
        responses.POST,
        f"{_BASE}/csrs",
        json={"requestId": "req-csr-2", "state": "INPROGRESS"},
        status=200,
    )
    fc.generate_csr(
        opts,
        "uuid-2",
        common_name="nsx01.example.com",
        organization="Acme",
        org_unit="Ops",
        locality="Rotterdam",
        state="ZH",
        country="NL",
    )
    spec = json.loads(vcfops_authed.calls[-1].request.body)["generateCsrSpec"]
    assert "email" not in spec
    assert "subjectAltNames" not in spec
    assert spec["keySize"] == "KEY_2048"
    assert spec["keyAlgorithm"] == "RSA"


# ---------------------------------------------------------------------------
# CA configuration
# ---------------------------------------------------------------------------


def test_get_certificate_authorities_returns_config(opts, vcfops_authed):
    ca_config = {"caType": "MSCA", "serverUrl": "https://dc1.example.com/certsrv"}
    vcfops_authed.add(
        responses.GET,
        f"{_BASE}/certificate-authorities",
        json=ca_config,
        status=200,
    )
    out = fc.get_certificate_authorities(opts)
    assert out == ca_config


def test_configure_certificate_authorities_sends_put(opts, vcfops_authed):
    config = {
        "caType": "MSCA",
        "serverUrl": "https://dc1.example.com/certsrv",
        "username": "svc-vcf",
        "password": "secret",
        "templateName": "VCFMachineSSL",
    }
    vcfops_authed.add(
        responses.PUT,
        f"{_BASE}/certificate-authorities",
        json=config,
        status=200,
    )
    out = fc.configure_certificate_authorities(opts, config)
    assert out == config
    body = json.loads(vcfops_authed.calls[-1].request.body)
    assert body["caType"] == "MSCA"
    assert body["templateName"] == "VCFMachineSSL"
