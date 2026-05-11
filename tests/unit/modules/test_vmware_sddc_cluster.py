"""Tests for modules.vmware_sddc_cluster."""

import pytest
import responses

from saltext.vmware.modules import vmware_sddc_cluster as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/clusters",
        json={"elements": [{"id": "c1"}]},
        status=200,
    )
    assert mod.list_() == {"elements": [{"id": "c1"}]}


def test_get(sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/clusters/c1", json={"id": "c1"}, status=200)
    assert mod.get("c1") == {"id": "c1"}


def test_create(sddc_authed):
    sddc_authed.add(
        responses.POST,
        "https://sm.test/v1/clusters",
        json={"id": "task-1"},
        status=202,
    )
    assert mod.create({"name": "c1"}) == {"id": "task-1"}


def test_delete(sddc_authed):
    sddc_authed.add(responses.DELETE, "https://sm.test/v1/clusters/c1", status=204)
    assert mod.delete("c1") == {}
