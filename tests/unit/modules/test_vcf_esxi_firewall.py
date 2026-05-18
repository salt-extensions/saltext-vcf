"""Tests for modules.vcf_esxi_firewall."""

import json

import pytest
import responses

from saltext.vcf.modules import vcf_esxi_firewall as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(esxi_authed):
    esxi_authed.add(responses.GET, "https://esxi.test/api/esx/firewall/rules", json=[], status=200)
    assert mod.list_() == []


def test_get(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/firewall/rules/sshServer",
        json={"name": "sshServer", "enabled": True},
        status=200,
    )
    assert mod.get("sshServer")["enabled"] is True


def test_set_enabled(esxi_authed):
    esxi_authed.add(
        responses.PATCH,
        "https://esxi.test/api/esx/firewall/rules/sshServer",
        status=204,
    )
    mod.set_enabled("sshServer", False)
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"enabled": False}


def test_set_allowed_ips(esxi_authed):
    esxi_authed.add(
        responses.PATCH,
        "https://esxi.test/api/esx/firewall/rules/sshServer",
        status=204,
    )
    mod.set_allowed_ips("sshServer", ["10.0.0.0/24"], all_ip=False)
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"allowed_hosts": {"all_ip": False, "ip_addresses": ["10.0.0.0/24"]}}
