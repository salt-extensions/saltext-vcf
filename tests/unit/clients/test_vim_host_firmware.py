"""Tests for clients.vim_host_firmware (backup/restore/reset)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import responses
from pyVmomi import vim

from saltext.vcf.clients import vim_host_firmware


def _fake_host(in_maintenance=False):
    h = MagicMock()
    h.name = "esxi-01"
    h.runtime.inMaintenanceMode = in_maintenance
    h.configManager.firmwareSystem.BackupFirmwareConfiguration.return_value = (
        "https://*//downloads/configBundle-esxi-01.tgz"
    )
    h.configManager.firmwareSystem.QueryFirmwareConfigUploadURL.return_value = (
        "https://*/uploadUrl/configBundle.tgz"
    )
    h.EnterMaintenanceMode_Task.return_value = MagicMock(_moId="task-mm-1")
    h.ExitMaintenanceMode_Task.return_value = MagicMock(_moId="task-mm-2")
    return h


@pytest.fixture
def factory(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(vim_host_firmware, "_resolve", lambda o, n, profile=None: holder["host"])
    monkeypatch.setattr("saltext.vcf.utils.vim.wait_for_task", lambda t, **kw: None)
    monkeypatch.setattr(
        "saltext.vcf.utils.esxi.get_config",
        lambda o, profile=None: {"host": "esxi-01", "username": "root", "password": "p"},
    )
    return holder


def test_backup_downloads_bundle(opts, factory, tmp_path):
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.GET, "https://esxi-01//downloads/configBundle-esxi-01.tgz", body=b"bundle-bytes")
        out = vim_host_firmware.backup(opts, "esxi-01", cachedir=str(tmp_path))
    assert out["esxi-01"]["file_name"].endswith("configBundle-esxi-01.tgz")
    assert (tmp_path / "configBundle-esxi-01.tgz").read_bytes() == b"bundle-bytes"
    import hashlib

    assert out["esxi-01"]["sha1"] == hashlib.sha1(b"bundle-bytes", usedforsecurity=False).hexdigest()


def test_restore_uploads_and_brackets_maintenance(opts, factory, tmp_path):
    bundle = tmp_path / "bundle.tgz"
    bundle.write_bytes(b"bundle-bytes")
    h = factory["host"]
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.PUT, "https://esxi-01/uploadUrl/configBundle.tgz", body=b"", status=200)
        out = vim_host_firmware.restore(opts, "esxi-01", str(bundle))
    assert out["esxi-01"] is True
    h.configManager.firmwareSystem.RestoreFirmwareConfiguration.assert_called_once_with(force=False)
    assert h.EnterMaintenanceMode_Task.called and h.ExitMaintenanceMode_Task.called


def test_restore_skips_maintenance_when_already_in(opts, factory, tmp_path):
    bundle = tmp_path / "bundle.tgz"
    bundle.write_bytes(b"bundle-bytes")
    h = factory["host"]
    h.runtime.inMaintenanceMode = True
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.PUT, "https://esxi-01/uploadUrl/configBundle.tgz", body=b"", status=200)
        vim_host_firmware.restore(opts, "esxi-01", str(bundle))
    h.EnterMaintenanceMode_Task.assert_not_called()


def test_reset_brackets_maintenance(opts, factory):
    h = factory["host"]
    out = vim_host_firmware.reset(opts, "esxi-01")
    assert out["esxi-01"] is True
    h.configManager.firmwareSystem.ResetFirmwareToFactoryDefaults.assert_called_once()
    assert h.ExitMaintenanceMode_Task.called
