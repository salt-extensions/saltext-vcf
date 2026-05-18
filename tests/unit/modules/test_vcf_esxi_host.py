"""Tests for modules.vcf_esxi_host."""

import json

import pytest
import responses

from saltext.vcf.modules import vcf_esxi_host as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_info(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/host",
        json={"version": "8.0.3", "build": "1234"},
        status=200,
    )
    assert mod.info() == {"version": "8.0.3", "build": "1234"}


def test_lockdown_get(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/host/lockdown",
        json={"mode": "NORMAL"},
        status=200,
    )
    assert mod.lockdown_get() == {"mode": "NORMAL"}


def test_lockdown_set_with_users(esxi_authed):
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/host/lockdown", status=204)
    mod.lockdown_set("STRICT", exception_users=["root"])
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"mode": "STRICT", "exception_users": ["root"]}


def test_enter_maintenance(esxi_authed):
    esxi_authed.add(responses.POST, "https://esxi.test/api/esx/host/maintenance", status=204)
    mod.enter_maintenance()
    assert "action=enter" in esxi_authed.calls[-1].request.url


def test_reboot_with_force(esxi_authed):
    esxi_authed.add(responses.POST, "https://esxi.test/api/esx/host/power", status=202)
    mod.reboot(force=True)
    last = esxi_authed.calls[-1].request
    assert "action=reboot" in last.url
    assert json.loads(last.body) == {"force": True}
