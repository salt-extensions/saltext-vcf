"""Tests for modules.vcf_esxi_advanced."""

import json

import pytest
import responses

from saltext.vcf.modules import vcf_esxi_advanced as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(esxi_authed):
    esxi_authed.add(responses.GET, "https://esxi.test/api/esx/advanced", json=[], status=200)
    assert mod.list_() == []


def test_get(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/advanced/Net.TcpipHeapMax",
        json={"key": "Net.TcpipHeapMax", "value": 512},
        status=200,
    )
    assert mod.get("Net.TcpipHeapMax")["value"] == 512


def test_set_value(esxi_authed):
    esxi_authed.add(
        responses.PATCH,
        "https://esxi.test/api/esx/advanced/Net.TcpipHeapMax",
        status=204,
    )
    mod.set_value("Net.TcpipHeapMax", 1024)
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"value": 1024}
