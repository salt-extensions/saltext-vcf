"""Tests for modules.vcf_nsx_tier0."""

import json

import pytest
import responses

from saltext.vcf.modules import vcf_nsx_tier0 as mod

BASE = "https://nsx.test/policy/api/v1/infra/tier-0s"


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        BASE,
        json={"results": [{"id": "t0-1"}]},
        status=200,
    )
    assert mod.list_() == {"results": [{"id": "t0-1"}]}


def test_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1",
        json={"id": "t0-1"},
        status=200,
    )
    assert mod.get("t0-1") == {"id": "t0-1"}


def test_bgp_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/default/bgp",
        json={"enabled": False},
        status=200,
    )
    assert mod.bgp_get("t0-1") == {"enabled": False}


def test_bgp_set(mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/bgp",
        json={"enabled": False},
        status=200,
    )
    mod.bgp_set("t0-1", False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}


def test_ospf_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/default/ospf",
        json={"enabled": False},
        status=200,
    )
    assert mod.ospf_get("t0-1") == {"enabled": False}


def test_ospf_set(mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/ospf",
        json={"enabled": False},
        status=200,
    )
    mod.ospf_set("t0-1", False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}


def test_multicast_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{BASE}/t0-1/locale-services/default/multicast",
        json={"enabled": False},
        status=200,
    )
    assert mod.multicast_get("t0-1") == {"enabled": False}


def test_multicast_set(mocked_responses):
    mocked_responses.add(
        responses.PATCH,
        f"{BASE}/t0-1/locale-services/default/multicast",
        json={"enabled": False},
        status=200,
    )
    mod.multicast_set("t0-1", False)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"enabled": False}
