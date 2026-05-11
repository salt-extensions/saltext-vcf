"""Tests for modules.vmware_nsx_tier0."""

import pytest
import responses

from saltext.vmware.modules import vmware_nsx_tier0 as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/tier-0s",
        json={"results": [{"id": "t0-1"}]},
        status=200,
    )
    assert mod.list_() == {"results": [{"id": "t0-1"}]}


def test_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/tier-0s/t0-1",
        json={"id": "t0-1"},
        status=200,
    )
    assert mod.get("t0-1") == {"id": "t0-1"}
