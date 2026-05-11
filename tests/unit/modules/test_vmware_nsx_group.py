"""Tests for modules.vmware_nsx_group."""

import json

import pytest
import responses

from saltext.vmware.modules import vmware_nsx_group as mod

_BASE = "https://nsx.test/policy/api/v1/infra/domains/default/groups"


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(mocked_responses):
    mocked_responses.add(responses.GET, _BASE, json={"results": []}, status=200)
    assert mod.list_() == {"results": []}


def test_get(mocked_responses):
    mocked_responses.add(responses.GET, f"{_BASE}/g-a", json={"id": "g-a"}, status=200)
    assert mod.get("g-a") == {"id": "g-a"}


def test_create_put(mocked_responses):
    mocked_responses.add(responses.PUT, f"{_BASE}/g-a", json={"id": "g-a"}, status=200)
    mod.create("g-a", expression=[{"resource_type": "Condition"}])
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "g-a"
    assert body["expression"]


def test_delete(mocked_responses):
    mocked_responses.add(responses.DELETE, f"{_BASE}/g-a", status=200)
    assert mod.delete("g-a") == {}
