"""Tests for clients.vim_host_passthrough."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import vim_host_passthrough


def _pci(pid, enabled=False, active=False, capable=True, vendor_name="ACME"):
    d = MagicMock()
    d.id = pid
    d.vendorId = 0x1234
    d.deviceId = 0x5678
    d.vendorName = vendor_name
    d.deviceName = f"dev-{pid}"
    d.passthruCapable = capable
    d.passthruEnabled = enabled
    d.passthruActive = active
    d.dependentDevice = None
    return d


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"host": MagicMock()}
    monkeypatch.setattr(vim_host_passthrough, "_host", lambda opts, h, profile=None: holder["host"])
    return holder


def test_list_returns_mapped_devices(opts, host_factory):
    pci_sys = host_factory["host"].configManager.pciPassthruSystem
    pci_sys.pciPassthruInfo = [
        _pci("0000:00:1f.0", enabled=False, active=False),
        _pci("0000:00:1f.1", enabled=True, active=False),
        _pci("0000:00:1f.2", enabled=True, active=True),
    ]
    out = vim_host_passthrough.list_(opts, "esx-1")
    assert out[0]["passthru_enabled"] is False
    # enabled but not active → reboot required
    assert out[1]["reboot_required"] is True
    # enabled and active → no reboot pending
    assert out[2]["reboot_required"] is False


def test_set_enabled_writes_config(opts, host_factory):
    pci_sys = host_factory["host"].configManager.pciPassthruSystem
    out = vim_host_passthrough.set_enabled(opts, "esx-1", "0000:00:1f.0", True)
    assert out == {"id": "0000:00:1f.0", "enabled": True, "reboot_required": True}
    pci_sys.UpdatePassthruConfig.assert_called_once()
    config = pci_sys.UpdatePassthruConfig.call_args.args[0][0]
    assert config.id == "0000:00:1f.0"
    assert config.passthruEnabled is True


def test_refresh_calls_through(opts, host_factory):
    pci_sys = host_factory["host"].configManager.pciPassthruSystem
    assert vim_host_passthrough.refresh(opts, "esx-1") is None
    pci_sys.Refresh.assert_called_once()
