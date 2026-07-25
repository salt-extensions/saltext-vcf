"""Tests for the NSX Tier-1 client (``saltext.vcf.clients.nsx_tier1``)."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import nsx_tier1

BASE = "https://nsx.test/policy/api/v1/infra/tier-1s"


def test_list_returns_results(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        BASE,
        json={"results": []},
        status=200,
    )
    assert nsx_tier1.list_(opts) == {"results": []}


def test_get_returns_gateway(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t1-a",
        json={"id": "t1-a"},
        status=200,
    )
    assert nsx_tier1.get(opts, "t1-a") == {"id": "t1-a"}


def test_get_or_none_returns_none_on_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/missing",
        json={"error_message": "not found"},
        status=404,
    )
    assert nsx_tier1.get_or_none(opts, "missing") is None


def test_get_or_none_reraises_non_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/boom",
        json={"error_message": "server error"},
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        nsx_tier1.get_or_none(opts, "boom")


def test_create_put(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        f"{BASE}/t1-a",
        json={"id": "t1-a"},
        status=200,
    )
    nsx_tier1.create(opts, "t1-a", tier0_path="/infra/tier-0s/t0-1")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "t1-a"
    assert body["tier0_path"] == "/infra/tier-0s/t0-1"


def test_delete(opts, mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        f"{BASE}/t1-a",
        status=200,
    )
    assert nsx_tier1.delete(opts, "t1-a") == {}


def test_multicast_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t1-a/locale-services/default/multicast",
        json={"enabled": True},
        status=200,
    )
    assert nsx_tier1.multicast_get(opts, "t1-a") == {"enabled": True}


def test_multicast_get_custom_locale_service(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t1-a/locale-services/ls-alt/multicast",
        json={"enabled": False},
        status=200,
    )
    assert nsx_tier1.multicast_get(opts, "t1-a", locale_service="ls-alt") == {"enabled": False}


def test_multicast_set_patches_enabled_false(opts, mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t1-a/locale-services/default/multicast",
        json={"enabled": False},
        status=200,
    )
    nsx_tier1.multicast_set(opts, "t1-a", False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}
    assert mocked_responses.calls[-1].request.method == "PATCH"
