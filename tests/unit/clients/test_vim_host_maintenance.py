"""Tests for clients.vim_host_maintenance (SOAP)."""

from unittest.mock import MagicMock

import pytest

from saltext.vmware.clients import vim_host_maintenance


@pytest.fixture
def host_factory(monkeypatch):
    h = MagicMock()
    h.runtime.inMaintenanceMode = False
    h.EnterMaintenanceMode_Task.return_value = MagicMock(_moId="task-enter")
    h.ExitMaintenanceMode_Task.return_value = MagicMock(_moId="task-exit")
    monkeypatch.setattr(vim_host_maintenance, "_host", lambda opts, name, profile=None: h)
    return h


def test_is_in_false(opts, host_factory):
    assert vim_host_maintenance.is_in(opts, "esx-1") is False


def test_is_in_true(opts, host_factory):
    host_factory.runtime.inMaintenanceMode = True
    assert vim_host_maintenance.is_in(opts, "esx-1") is True


def test_enter_basic(opts, host_factory):
    out = vim_host_maintenance.enter(opts, "esx-1", evacuate_powered_off_vms=True, timeout=300)
    assert out == "task-enter"
    kwargs = host_factory.EnterMaintenanceMode_Task.call_args.kwargs
    assert kwargs["timeout"] == 300
    assert kwargs["evacuatePoweredOffVms"] is True
    assert "maintenanceSpec" not in kwargs


def test_enter_with_vsan_mode(opts, host_factory):
    vim_host_maintenance.enter(opts, "esx-1", vsan_mode="ensureObjectAccessibility")
    kwargs = host_factory.EnterMaintenanceMode_Task.call_args.kwargs
    assert "maintenanceSpec" in kwargs


def test_exit_(opts, host_factory):
    assert vim_host_maintenance.exit_(opts, "esx-1", timeout=120) == "task-exit"
    host_factory.ExitMaintenanceMode_Task.assert_called_with(timeout=120)
