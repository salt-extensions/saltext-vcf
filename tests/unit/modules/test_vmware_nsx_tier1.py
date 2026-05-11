"""Tests for modules.vmware_nsx_tier1."""

import json

import pytest
import responses

from saltext.vmware.modules import vmware_nsx_tier1 as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/tier-1s",
        json={"results": []},
        status=200,
    )
    assert mod.list_() == {"results": []}


def test_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/tier-1s/t1-a",
        json={"id": "t1-a"},
        status=200,
    )
    assert mod.get("t1-a") == {"id": "t1-a"}


def test_create_put(mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/tier-1s/t1-a",
        json={"id": "t1-a"},
        status=200,
    )
    mod.create("t1-a", tier0_path="/infra/tier-0s/t0-1")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "t1-a"
    assert body["tier0_path"] == "/infra/tier-0s/t0-1"


def test_delete(mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        "https://nsx.test/policy/api/v1/infra/tier-1s/t1-a",
        status=200,
    )
    assert mod.delete("t1-a") == {}
