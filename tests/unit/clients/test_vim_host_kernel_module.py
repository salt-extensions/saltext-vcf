"""Tests for clients.vim_host_kernel_module."""

from unittest.mock import MagicMock

import pytest

from saltext.vmware.clients import vim_host_kernel_module


def _module(name, version="1.0", loaded=True, enabled=True, use_count=0, deps=None):
    m = MagicMock()
    m.name = name
    m.version = version
    m.loaded = loaded
    m.enabled = enabled
    m.useCount = use_count
    m.modulesDependent = deps or []
    return m


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"host": MagicMock()}

    def _patched(opts, h, profile=None):
        return holder["host"]

    monkeypatch.setattr(vim_host_kernel_module, "_host", _patched)
    return holder


def test_list_returns_mapped_modules(opts, host_factory):
    km = host_factory["host"].configManager.kernelModuleSystem
    km.QueryModules.return_value = [_module("vmkernel"), _module("nfs41", use_count=2)]
    out = vim_host_kernel_module.list_(opts, "esx-1")
    assert len(out) == 2
    assert out[0]["name"] == "vmkernel"
    assert out[1]["use_count"] == 2


def test_get_options(opts, host_factory):
    km = host_factory["host"].configManager.kernelModuleSystem
    km.QueryConfiguredModuleOptionString.return_value = "max_vfs=8"
    assert vim_host_kernel_module.get_options(opts, "esx-1", "ixgbe") == "max_vfs=8"
    km.QueryConfiguredModuleOptionString.assert_called_with(name="ixgbe")


def test_set_options(opts, host_factory):
    km = host_factory["host"].configManager.kernelModuleSystem
    out = vim_host_kernel_module.set_options(opts, "esx-1", "ixgbe", "max_vfs=8")
    assert out == {"name": "ixgbe", "options": "max_vfs=8"}
    km.UpdateModuleOptionString.assert_called_with(name="ixgbe", options="max_vfs=8")


def test_raises_when_no_manager(opts, monkeypatch):
    host = MagicMock()
    host.configManager.kernelModuleSystem = None
    host.name = "esx-1"
    monkeypatch.setattr(vim_host_kernel_module, "_host", lambda opts, h, profile=None: host)
    with pytest.raises(RuntimeError, match="kernelModuleSystem"):
        vim_host_kernel_module.list_(opts, "esx-1")
