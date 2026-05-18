"""Tests for saltext.vcf.utils.nsx."""

import pytest
import responses

from saltext.vcf.utils import nsx


def test_get_config_default(opts):
    cfg = nsx.get_config(opts)
    assert cfg == {
        "host": "nsx.test",
        "username": "u",
        "password": "p",
        "verify_ssl": False,
    }


def test_get_config_profile_falls_back_when_missing(opts):
    cfg = nsx.get_config(opts, profile="alt")
    assert cfg["host"] == "nsx.test"


def test_basic_auth_sent_per_request(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/segments",
        json={"results": []},
        status=200,
    )
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/segments",
        json={"results": []},
        status=200,
    )
    nsx.api_get(opts, "/policy/api/v1/infra/segments")
    nsx.api_get(opts, "/policy/api/v1/infra/segments")
    for call in mocked_responses.calls:
        assert call.request.headers["Authorization"].startswith("Basic ")


def test_api_put(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/segments/seg-a",
        json={"id": "seg-a"},
        status=200,
    )
    assert nsx.api_put(
        opts, "/policy/api/v1/infra/segments/seg-a", body={"display_name": "seg-a"}
    ) == {"id": "seg-a"}


def test_api_delete(opts, mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        "https://nsx.test/policy/api/v1/infra/segments/seg-a",
        status=204,
    )
    assert nsx.api_delete(opts, "/policy/api/v1/infra/segments/seg-a") == {}


def test_error_propagates(opts, mocked_responses):
    import requests

    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/segments/missing",
        status=404,
    )
    with pytest.raises(requests.HTTPError):
        nsx.api_get(opts, "/policy/api/v1/infra/segments/missing")
