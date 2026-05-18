"""Tests for saltext.vcf.utils.vcfops."""

import json

import pytest
import responses

from saltext.vcf.utils import vcfops


def test_get_config_default(opts):
    cfg = vcfops.get_config(opts)
    assert cfg["host"] == "ops.test"
    assert cfg["auth_source"] == "LOCAL"
    assert cfg["verify_ssl"] is False


def test_token_caches(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        json={"token": "t1"},
        status=200,
    )
    mocked_responses.add(
        responses.GET, "https://ops.test/suite-api/api/versions", json={}, status=200
    )
    mocked_responses.add(
        responses.GET, "https://ops.test/suite-api/api/resources", json={}, status=200
    )
    vcfops.api_get(opts, "/suite-api/api/versions")
    vcfops.api_get(opts, "/suite-api/api/resources")
    auth_calls = [c for c in mocked_responses.calls if "/auth/token/acquire" in c.request.url]
    assert len(auth_calls) == 1


def test_auth_body_includes_auth_source(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        json={"token": "t"},
        status=200,
    )
    mocked_responses.add(
        responses.GET, "https://ops.test/suite-api/api/versions", json={}, status=200
    )
    vcfops.api_get(opts, "/suite-api/api/versions")
    body = json.loads(mocked_responses.calls[0].request.body)
    assert body == {"username": "admin", "password": "p", "authSource": "LOCAL"}


def test_session_uses_vRealizeOpsToken_header(
    opts, vcfops_authed
):  # noqa: N802  pylint: disable=invalid-name
    vcfops_authed.add(responses.GET, "https://ops.test/suite-api/api/versions", json={}, status=200)
    vcfops.api_get(opts, "/suite-api/api/versions")
    assert (
        vcfops_authed.calls[-1].request.headers["Authorization"] == "vRealizeOpsToken ops-tok-abc"
    )


def test_invalidate_token(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        json={"token": "t1"},
        status=200,
    )
    mocked_responses.add(
        responses.GET, "https://ops.test/suite-api/api/versions", json={}, status=200
    )
    mocked_responses.add(
        responses.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        json={"token": "t2"},
        status=200,
    )
    mocked_responses.add(
        responses.GET, "https://ops.test/suite-api/api/versions", json={}, status=200
    )
    vcfops.api_get(opts, "/suite-api/api/versions")
    vcfops.invalidate_token(opts)
    vcfops.api_get(opts, "/suite-api/api/versions")
    auth_calls = [c for c in mocked_responses.calls if "/auth/token/acquire" in c.request.url]
    assert len(auth_calls) == 2


def test_http_error_propagates(opts, vcfops_authed):
    import requests

    vcfops_authed.add(responses.GET, "https://ops.test/suite-api/api/versions", status=500)
    with pytest.raises(requests.HTTPError):
        vcfops.api_get(opts, "/suite-api/api/versions")
