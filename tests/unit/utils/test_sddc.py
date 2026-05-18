"""Tests for saltext.vcf.utils.sddc."""

import pytest
import responses

from saltext.vcf.utils import sddc


def test_get_config_default(opts):
    cfg = sddc.get_config(opts)
    assert cfg["host"] == "sm.test"
    assert cfg["verify_ssl"] is False


def test_token_cached(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://sm.test/v1/tokens",
        json={"accessToken": "jwt-1"},
        status=200,
    )
    mocked_responses.add(
        responses.GET, "https://sm.test/v1/hosts", json={"elements": []}, status=200
    )
    mocked_responses.add(
        responses.GET, "https://sm.test/v1/domains", json={"elements": []}, status=200
    )

    sddc.api_get(opts, "/v1/hosts")
    sddc.api_get(opts, "/v1/domains")

    auth_calls = [c for c in mocked_responses.calls if "v1/tokens" in c.request.url]
    assert len(auth_calls) == 1


def test_invalidate_token_forces_reauth(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://sm.test/v1/tokens",
        json={"accessToken": "jwt-1"},
        status=200,
    )
    mocked_responses.add(responses.GET, "https://sm.test/v1/hosts", json={}, status=200)
    mocked_responses.add(
        responses.POST,
        "https://sm.test/v1/tokens",
        json={"accessToken": "jwt-2"},
        status=200,
    )
    mocked_responses.add(responses.GET, "https://sm.test/v1/hosts", json={}, status=200)

    sddc.api_get(opts, "/v1/hosts")
    sddc.invalidate_token(opts)
    sddc.api_get(opts, "/v1/hosts")
    auth_calls = [c for c in mocked_responses.calls if "v1/tokens" in c.request.url]
    assert len(auth_calls) == 2


def test_api_post_sends_bearer(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        "https://sm.test/v1/clusters",
        json={"id": "c1"},
        status=202,
    )
    result = sddc.api_post(opts, "/v1/clusters", body={"name": "c1"})
    assert result == {"id": "c1"}
    last = sddc_authed.calls[-1]
    assert last.request.headers["Authorization"] == "Bearer jwt-abc"


def test_api_patch(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        "https://sm.test/v1/credentials",
        json={"id": "task-1"},
        status=202,
    )
    assert sddc.api_patch(opts, "/v1/credentials", body={"op": "ROTATE"}) == {"id": "task-1"}


def test_api_delete(opts, sddc_authed):
    sddc_authed.add(responses.DELETE, "https://sm.test/v1/hosts/h1", status=204)
    assert sddc.api_delete(opts, "/v1/hosts/h1") == {}


def test_error_propagates(opts, sddc_authed):
    import requests

    sddc_authed.add(responses.GET, "https://sm.test/v1/hosts/nope", status=404)
    with pytest.raises(requests.HTTPError):
        sddc.api_get(opts, "/v1/hosts/nope")
