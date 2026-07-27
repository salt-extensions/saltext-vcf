"""Tests for modules.vcf_esxi_ad_auth."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import esxi_ad_auth as client
from saltext.vcf.modules import vcf_esxi_ad_auth as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_get_ad_state_delegates(monkeypatch, opts):
    called = {}

    def _fake(o, host, profile=None):
        called["args"] = (o, host, profile)
        return {"joined": False}

    monkeypatch.setattr(client, "get_ad_state", _fake)
    assert mod.get_ad_state("esxi-01") == {"joined": False}
    assert called["args"][1] == "esxi-01"
    assert called["args"][2] is None


def test_join_domain_delegates(monkeypatch, opts):
    seen = MagicMock(return_value="task-1")
    monkeypatch.setattr(client, "join_domain", seen)
    assert mod.join_domain("esxi-01", "corp.example.com", "u", "p", profile="alt") == "task-1"
    seen.assert_called_once_with(opts, "esxi-01", "corp.example.com", "u", "p", profile="alt")


def test_leave_domain_delegates(monkeypatch, opts):
    seen = MagicMock(return_value="task-2")
    monkeypatch.setattr(client, "leave_domain", seen)
    assert mod.leave_domain("esxi-01", force=True) == "task-2"
    seen.assert_called_once_with(opts, "esxi-01", force=True, profile=None)
