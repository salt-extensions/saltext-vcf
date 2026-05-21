"""Tests for modules.vcf_esxi_host."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_esxi_host as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def _fake_host(
    *, version="8.0.3", build="1234", vendor="Dell", model="R740", lockdown="lockdownNormal"
):
    host = MagicMock()
    host.summary.config.product.version = version
    host.summary.config.product.build = build
    host.summary.config.product.name = "VMware ESXi"
    host.summary.runtime.inMaintenanceMode = False
    host.summary.runtime.connectionState = "connected"
    host.summary.runtime.powerState = "poweredOn"
    host.hardware.systemInfo.vendor = vendor
    host.hardware.systemInfo.model = model
    host.configManager.hostAccessManager.lockdownMode = lockdown
    return host


def test_info():
    host = _fake_host()
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        info = mod.info()
    assert info["version"] == "8.0.3"
    assert info["build"] == "1234"
    assert info["vendor"] == "Dell"
    assert info["model"] == "R740"
    assert info["in_maintenance_mode"] is False


def test_lockdown_get():
    host = _fake_host(lockdown="lockdownNormal")
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.lockdown_get() == {"mode": "NORMAL"}


def test_lockdown_set_with_users():
    host = _fake_host(lockdown="lockdownStrict")
    mgr = host.configManager.hostAccessManager
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.lockdown_set("STRICT", exception_users=["root"])
    mgr.ChangeLockdownMode.assert_called_once_with(mode="lockdownStrict")
    mgr.UpdateLockdownExceptions.assert_called_once_with(users=["root"])


def test_enter_maintenance():
    host = _fake_host()
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.enter_maintenance()
    assert result == {"status": "entering maintenance"}
    host.EnterMaintenanceMode_Task.assert_called_once_with(timeout=0)


def test_reboot_with_force():
    host = _fake_host()
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.reboot(force=True)
    assert result == {"status": "rebooting"}
    host.RebootHost_Task.assert_called_once_with(force=True)
