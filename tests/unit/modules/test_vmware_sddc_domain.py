"""Tests for modules.vmware_sddc_domain."""

import pytest
import responses

from saltext.vmware.modules import vmware_sddc_domain as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/domains",
        json={"elements": []},
        status=200,
    )
    assert mod.list_() == {"elements": []}


def test_get(sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/domains/mgmt",
        json={"id": "mgmt"},
        status=200,
    )
    assert mod.get("mgmt") == {"id": "mgmt"}
