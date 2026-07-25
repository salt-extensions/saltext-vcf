"""Tests for the NSX Tier-0 client (``saltext.vcf.clients.nsx_tier0``)."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import nsx_tier0

BASE = "https://nsx.test/policy/api/v1/infra/tier-0s"


def test_list_returns_results(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        BASE,
        json={"results": [{"id": "t0-1"}]},
        status=200,
    )
    assert nsx_tier0.list_(opts) == {"results": [{"id": "t0-1"}]}


def test_get_returns_gateway(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1",
        json={"id": "t0-1"},
        status=200,
    )
    assert nsx_tier0.get(opts, "t0-1") == {"id": "t0-1"}


def test_get_or_none_returns_gateway(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1",
        json={"id": "t0-1"},
        status=200,
    )
    assert nsx_tier0.get_or_none(opts, "t0-1") == {"id": "t0-1"}


def test_get_or_none_returns_none_on_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/missing",
        json={"error_message": "not found"},
        status=404,
    )
    assert nsx_tier0.get_or_none(opts, "missing") is None


def test_get_or_none_reraises_non_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/boom",
        json={"error_message": "server error"},
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        nsx_tier0.get_or_none(opts, "boom")


def test_bgp_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/default/bgp",
        json={"enabled": True},
        status=200,
    )
    assert nsx_tier0.bgp_get(opts, "t0-1") == {"enabled": True}


def test_bgp_get_custom_locale_service(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/edge-ls/bgp",
        json={"enabled": False},
        status=200,
    )
    assert nsx_tier0.bgp_get(opts, "t0-1", locale_service="edge-ls") == {"enabled": False}


def test_bgp_set_patches_enabled_false(opts, mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/bgp",
        json={"enabled": False},
        status=200,
    )
    result = nsx_tier0.bgp_set(opts, "t0-1", False)
    assert result == {"enabled": False}
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}


def test_bgp_set_passes_extras(opts, mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/bgp",
        json={"enabled": True, "ecmp": True},
        status=200,
    )
    nsx_tier0.bgp_set(opts, "t0-1", True, ecmp=True)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": True, "ecmp": True}


def test_ospf_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/default/ospf",
        json={"enabled": True},
        status=200,
    )
    assert nsx_tier0.ospf_get(opts, "t0-1") == {"enabled": True}


def test_ospf_set_patches_enabled_false(opts, mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/ospf",
        json={"enabled": False},
        status=200,
    )
    nsx_tier0.ospf_set(opts, "t0-1", False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}
    assert mocked_responses.calls[-1].request.method == "PATCH"


def test_multicast_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/default/multicast",
        json={"enabled": False},
        status=200,
    )
    assert nsx_tier0.multicast_get(opts, "t0-1") == {"enabled": False}


def test_multicast_set_patches_enabled_false(opts, mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/multicast",
        json={"enabled": False},
        status=200,
    )
    nsx_tier0.multicast_set(opts, "t0-1", False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}
