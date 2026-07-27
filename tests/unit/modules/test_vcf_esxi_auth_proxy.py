"""Tests for modules.vcf_esxi_auth_proxy."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import esxi_auth_proxy as client
from saltext.vcf.modules import vcf_esxi_auth_proxy as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_get_config_delegates(monkeypatch, opts):
    called = {}

    def _fake(o, host, profile=None):
        called["args"] = (o, host, profile)
        return {"ok": True}

    monkeypatch.setattr(client, "get_config", _fake)
    assert mod.get_config("esxi-01") == {"ok": True}
    assert called["args"][1] == "esxi-01"
    assert called["args"][2] is None


def test_set_config_delegates(monkeypatch, opts):
    seen = MagicMock(return_value={"cam_address": "cam", "verify_cam_cert": True})
    monkeypatch.setattr(client, "set_config", seen)
    mod.set_config("esxi-01", cam_address="cam", verify_cam_cert=True)
    seen.assert_called_once_with(
        opts, "esxi-01", cam_address="cam", verify_cam_cert=True, profile=None
    )


def test_join_domain_via_cam_delegates(monkeypatch, opts):
    seen = MagicMock(return_value="task-1")
    monkeypatch.setattr(client, "join_domain_via_cam", seen)
    assert mod.join_domain_via_cam("esxi-01", "corp.example.com", "cam.example.com") == "task-1"
    seen.assert_called_once_with(
        opts, "esxi-01", "corp.example.com", "cam.example.com", profile=None
    )


def test_leave_domain_delegates(monkeypatch, opts):
    seen = MagicMock(return_value="task-2")
    monkeypatch.setattr(client, "leave_domain", seen)
    assert mod.leave_domain("esxi-01", force=True) == "task-2"
    seen.assert_called_once_with(opts, "esxi-01", force=True, profile=None)
