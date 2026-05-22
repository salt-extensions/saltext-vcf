"""Tests for clients.vcfops_certificate."""

import pytest
import responses

from saltext.vcf.clients import vcfops_certificate as cc

_URL = "https://ops.test/suite-api/api/certificate"


def _cert(thumbprint, issued_to="CN=vc.test"):
    return {
        "thumbprint": thumbprint,
        "certificateDetails": "issuer=CA expires=2027",
        "issuedTo": issued_to,
        "issuedBy": "CN=CA",
    }


def test_list_returns_certificates_array(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        _URL,
        json={"certificates": [_cert("AA"), _cert("BB")]},
        status=200,
    )
    out = cc.list_(opts)
    assert [c["thumbprint"] for c in out] == ["AA", "BB"]


def test_list_handles_missing_certificates_key(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _URL, json={}, status=200)
    assert cc.list_(opts) == []


def test_get_returns_match(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        _URL,
        json={"certificates": [_cert("AA"), _cert("BB")]},
        status=200,
    )
    assert cc.get(opts, "BB")["thumbprint"] == "BB"


def test_get_raises_when_missing(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _URL, json={"certificates": [_cert("AA")]}, status=200)
    with pytest.raises(KeyError):
        cc.get(opts, "ZZ")


def test_get_or_none_returns_none_when_missing(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, _URL, json={"certificates": [_cert("AA")]}, status=200)
    assert cc.get_or_none(opts, "ZZ") is None


def test_delete_sends_thumbprint_query_param(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, _URL, status=204)
    cc.delete(opts, "AABB", force=False)
    url = vcfops_authed.calls[-1].request.url
    assert "thumbprint=AABB" in url
    assert "force=false" in url


def test_delete_sets_force_true(opts, vcfops_authed):
    vcfops_authed.add(responses.DELETE, _URL, status=204)
    cc.delete(opts, "AABB", force=True)
    assert "force=true" in vcfops_authed.calls[-1].request.url
