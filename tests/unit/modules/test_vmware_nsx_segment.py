"""Tests for modules.vmware_nsx_segment."""

import json

import pytest
import responses

from saltext.vmware.modules import vmware_nsx_segment as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/segments",
        json={"results": []},
        status=200,
    )
    assert mod.list_() == {"results": []}


def test_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/segments/seg-a",
        json={"id": "seg-a"},
        status=200,
    )
    assert mod.get("seg-a") == {"id": "seg-a"}


def test_create_uses_put_with_display_name(mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/segments/seg-a",
        json={"id": "seg-a"},
        status=200,
    )
    mod.create("seg-a", transport_zone_path="/infra/sites/default/tz-1")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "seg-a"
    assert body["transport_zone_path"] == "/infra/sites/default/tz-1"


def test_delete(mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        "https://nsx.test/policy/api/v1/infra/segments/seg-a",
        status=200,
    )
    assert mod.delete("seg-a") == {}
