"""Tests for clients.vim_host_vmotion (HostVMotionSystem)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vim_host_vmotion


def _fake_host(selected_device=None):
    h = MagicMock()
    h.name = "esxi-01"
    vm = h.configManager.vmotionSystem
    net_config = vm.config.netConfig
    net_config.selectedVnic = None
    if selected_device is not None:
        selected = MagicMock()
        selected.device = selected_device
        net_config.selectedVnic = selected
    return h


@pytest.fixture
def factory(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(vim_host_vmotion, "_resolve", lambda o, n, profile=None: holder["host"])
    return holder


def test_get_disabled(opts, factory):
    assert vim_host_vmotion.get_enabled(opts, "esxi-01") == {"enabled": False, "device": None}


def test_get_enabled(opts, factory):
    factory["host"] = _fake_host("vmk1")
    assert vim_host_vmotion.get_enabled(opts, "esxi-01") == {"enabled": True, "device": "vmk1"}


def test_enable_selects_vnic(opts, factory):
    out = vim_host_vmotion.enable(opts, "esxi-01", device="vmk1")
    assert out == {"enabled": True, "device": "vmk1"}
    factory["host"].configManager.vmotionSystem.SelectVnic.assert_called_once_with(device="vmk1")


def test_disable_deselects(opts, factory):
    factory["host"] = _fake_host("vmk1")
    out = vim_host_vmotion.disable(opts, "esxi-01")
    assert out == {"enabled": False, "device": None}
    factory["host"].configManager.vmotionSystem.DeselectVnic.assert_called_once()


def test_disable_noop_when_not_enabled(opts, factory):
    out = vim_host_vmotion.disable(opts, "esxi-01")
    assert out == {"enabled": False, "device": None}
    factory["host"].configManager.vmotionSystem.DeselectVnic.assert_not_called()
