"""Tests for clients.vim_host_powermgmt."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import vim_host_powermgmt


def _policy(key, short, name=None, description=""):
    p = MagicMock()
    p.key = key
    p.shortName = short
    p.name = name or short
    p.description = description
    return p


@pytest.fixture
def host_factory(monkeypatch):
    host = MagicMock()
    monkeypatch.setattr(vim_host_powermgmt, "_host", lambda opts, h, profile=None: host)
    return host


def test_list_policies(opts, host_factory):
    ps = host_factory.configManager.powerSystem
    ps.capability.availablePolicy = [
        _policy(1, "high-performance"),
        _policy(2, "balanced"),
        _policy(3, "low-power"),
        _policy(4, "custom"),
    ]
    out = vim_host_powermgmt.list_policies(opts, "esx-1")
    assert {p["short_name"] for p in out} == {"high-performance", "balanced", "low-power", "custom"}
    assert all(isinstance(p["key"], int) for p in out)


def test_get_policy(opts, host_factory):
    ps = host_factory.configManager.powerSystem
    ps.info.currentPolicy = _policy(2, "balanced")
    out = vim_host_powermgmt.get_policy(opts, "esx-1")
    assert out["short_name"] == "balanced"
    assert out["key"] == 2


def test_set_policy(opts, host_factory):
    ps = host_factory.configManager.powerSystem
    ps.info.currentPolicy = _policy(2, "balanced")
    out = vim_host_powermgmt.set_policy(opts, "esx-1", 2)
    ps.ConfigurePowerPolicy.assert_called_with(key=2)
    assert out["key"] == 2
