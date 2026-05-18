"""Tests for modules.vcf_esxi_ntp."""

import json

import pytest
import responses

from saltext.vcf.modules import vcf_esxi_ntp as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_get(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/ntp",
        json={"servers": ["a"], "enabled": True},
        status=200,
    )
    assert mod.get() == {"servers": ["a"], "enabled": True}


def test_set_servers(esxi_authed):
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/ntp", status=204)
    mod.set_servers(["pool.ntp.org", "time.cloudflare.com"])
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"servers": ["pool.ntp.org", "time.cloudflare.com"]}


def test_set_enabled(esxi_authed):
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/ntp", status=204)
    mod.set_enabled(False)
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"enabled": False}
