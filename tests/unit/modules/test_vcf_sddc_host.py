"""Tests for modules.vcf_sddc_host."""

import pytest
import responses

from saltext.vcf.modules import vcf_sddc_host as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(sddc_authed):
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/hosts",
        json={"elements": []},
        status=200,
    )
    assert mod.list_() == {"elements": []}


def test_get(sddc_authed):
    sddc_authed.add(responses.GET, "https://sm.test/v1/hosts/h1", json={"id": "h1"}, status=200)
    assert mod.get("h1") == {"id": "h1"}


def test_commission(sddc_authed):
    sddc_authed.add(
        responses.POST,
        "https://sm.test/v1/hosts",
        json={"id": "task-1"},
        status=202,
    )
    assert mod.commission([{"hostfqdn": "esxi01"}]) == {"id": "task-1"}


def test_decommission(sddc_authed):
    sddc_authed.add(responses.DELETE, "https://sm.test/v1/hosts/h1", status=204)
    assert mod.decommission("h1") == {}
