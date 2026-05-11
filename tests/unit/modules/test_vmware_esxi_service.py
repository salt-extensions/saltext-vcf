"""Tests for modules.vmware_esxi_service."""

import json

import pytest
import responses

from saltext.vmware.modules import vmware_esxi_service as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/services",
        json=[{"name": "TSM-SSH"}],
        status=200,
    )
    assert mod.list_() == [{"name": "TSM-SSH"}]


def test_get(esxi_authed):
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/services/TSM-SSH",
        json={"state": "RUNNING", "startup_policy": "ON"},
        status=200,
    )
    assert mod.get("TSM-SSH") == {"state": "RUNNING", "startup_policy": "ON"}


@pytest.mark.parametrize(
    "fn,action", [("start", "start"), ("stop", "stop"), ("restart", "restart")]
)
def test_actions(esxi_authed, fn, action):
    esxi_authed.add(responses.POST, "https://esxi.test/api/esx/services/TSM-SSH", status=204)
    getattr(mod, fn)("TSM-SSH")
    assert f"action={action}" in esxi_authed.calls[-1].request.url


def test_set_policy(esxi_authed):
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/services/TSM-SSH", status=204)
    mod.set_policy("TSM-SSH", "AUTOMATIC")
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"startup_policy": "AUTOMATIC"}


def test_set_policy_rejects_bad_value(esxi_authed):
    with pytest.raises(ValueError):
        mod.set_policy("TSM-SSH", "BOGUS")
