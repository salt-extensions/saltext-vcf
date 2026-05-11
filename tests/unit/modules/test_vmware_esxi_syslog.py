"""Tests for modules.vmware_esxi_syslog."""

import json

import pytest
import responses

from saltext.vmware.modules import vmware_esxi_syslog as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_get(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/syslog",
        json={"servers": ["udp://collector:514"], "log_level": "INFO"},
        status=200,
    )
    assert mod.get()["log_level"] == "INFO"


def test_set_servers(esxi_authed):
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/syslog", status=204)
    mod.set_servers(["udp://collector:514"])
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"servers": ["udp://collector:514"]}


def test_set_log_level(esxi_authed):
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/syslog", status=204)
    mod.set_log_level("DEBUG")
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"log_level": "DEBUG"}
