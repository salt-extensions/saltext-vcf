"""Tests for clients.vim_host_security (lockdown / users / iSCSI via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_host_security


def _fake_host(
    lockdown_mode="lockdownDisabled",
    exception_users=None,
    has_access_manager=True,
    iscsi_hba=None,
):
    h = MagicMock()
    h.config.lockdownMode = lockdown_mode
    h.config.adminDisabled = False
    if has_access_manager:
        am = MagicMock()
        am.QueryLockdownExceptions.return_value = list(exception_users or [])
        h.configManager.hostAccessManager = am
    else:
        h.configManager.hostAccessManager = None
    storage = MagicMock()
    h.configManager.storageSystem = storage
    if iscsi_hba is None:
        storage.storageDeviceInfo.hostBusAdapter = []
    else:
        storage.storageDeviceInfo.hostBusAdapter = [iscsi_hba]
    h.configManager.accountManager = MagicMock()
    return h


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(vim_host_security, "_host", lambda opts, h, profile=None: holder["host"])
    return holder


# ---------- lockdown ----------


def test_lockdown_get_disabled_default(host_factory, opts):
    result = vim_host_security.lockdown_get(opts, "esxi-01")
    assert result["mode"] == "lockdownDisabled"
    assert result["exception_users"] == []


def test_lockdown_get_includes_exception_users(host_factory, opts):
    host_factory["host"] = _fake_host(
        lockdown_mode="lockdownNormal", exception_users=["root", "ops"]
    )
    result = vim_host_security.lockdown_get(opts, "esxi-01")
    assert result["mode"] == "lockdownNormal"
    assert result["exception_users"] == ["root", "ops"]


def test_lockdown_set(host_factory, opts):
    vim_host_security.lockdown_set(opts, "esxi-01", "lockdownStrict")
    host_factory["host"].configManager.hostAccessManager.ChangeLockdownMode.assert_called_once_with(
        mode="lockdownStrict"
    )


def test_lockdown_set_exception_users(host_factory, opts):
    vim_host_security.lockdown_set_exception_users(opts, "esxi-01", ["root", "ops"])
    host_factory[
        "host"
    ].configManager.hostAccessManager.UpdateLockdownExceptions.assert_called_once_with(
        users=["root", "ops"]
    )


# ---------- local users ----------


def test_user_create_passes_account_spec(host_factory, opts):
    vim_host_security.user_create(opts, "esxi-01", "ops", "secret", description="ops user")
    call = host_factory["host"].configManager.accountManager.CreateUser.call_args
    spec = call.kwargs["user"]
    assert spec.id == "ops"
    assert spec.password == "secret"
    assert spec.description == "ops user"


def test_user_update_only_changes_provided_fields(host_factory, opts):
    vim_host_security.user_update(opts, "esxi-01", "ops", password="newpw")
    spec = host_factory["host"].configManager.accountManager.UpdateUser.call_args.kwargs["user"]
    assert spec.id == "ops"
    assert spec.password == "newpw"
    assert spec.description is None


def test_user_delete(host_factory, opts):
    vim_host_security.user_delete(opts, "esxi-01", "ops")
    host_factory["host"].configManager.accountManager.RemoveUser.assert_called_once_with(
        userName="ops"
    )


# ---------- iSCSI ----------


def _iscsi_hba(device="vmhba33", iqn="iqn.test.x", static=(), send=(), chap=False):
    hba = vim.host.InternetScsiHba()
    hba.device = device
    hba.iScsiName = iqn
    hba.configuredStaticTarget = [
        vim.host.InternetScsiHba.StaticTarget(
            address=t["address"], port=t["port"], iScsiName=t["iqn"]
        )
        for t in static
    ]
    hba.configuredSendTarget = [
        vim.host.InternetScsiHba.SendTarget(address=t["address"], port=t["port"]) for t in send
    ]
    auth = vim.host.InternetScsiHba.AuthenticationProperties(
        chapAuthEnabled=bool(chap),
    )
    hba.authenticationProperties = auth
    return hba


def test_iscsi_status_disabled_when_no_hba(host_factory, opts):
    result = vim_host_security.iscsi_status(opts, "esxi-01")
    assert result == {
        "enabled": False,
        "hba_device": None,
        "iqn": None,
        "static_targets": [],
        "send_targets": [],
        "auth_type": "none",
    }


def test_iscsi_status_includes_targets(host_factory, opts):
    hba = _iscsi_hba(
        send=[{"address": "10.0.0.50", "port": 3260}],
        static=[{"address": "10.0.0.51", "port": 3260, "iqn": "iqn.test.lun1"}],
    )
    host_factory["host"] = _fake_host(iscsi_hba=hba)
    result = vim_host_security.iscsi_status(opts, "esxi-01")
    assert result["enabled"] is True
    assert result["hba_device"] == "vmhba33"
    assert result["iqn"] == "iqn.test.x"
    assert result["send_targets"][0]["address"] == "10.0.0.50"
    assert result["static_targets"][0]["iqn"] == "iqn.test.lun1"
    assert result["auth_type"] == "none"


def test_iscsi_status_reports_chap(host_factory, opts):
    hba = _iscsi_hba(chap=True)
    host_factory["host"] = _fake_host(iscsi_hba=hba)
    assert vim_host_security.iscsi_status(opts, "esxi-01")["auth_type"] == "chap"


def test_iscsi_enable_returns_hba_device(host_factory, opts):
    hba = _iscsi_hba()
    host_factory["host"] = _fake_host(iscsi_hba=hba)
    device = vim_host_security.iscsi_enable(opts, "esxi-01")
    assert device == "vmhba33"
    host_factory[
        "host"
    ].configManager.storageSystem.UpdateSoftwareInternetScsiEnabled.assert_called_once_with(
        enabled=True
    )
    host_factory["host"].configManager.storageSystem.RescanAllHba.assert_called_once()


def test_iscsi_disable(host_factory, opts):
    vim_host_security.iscsi_disable(opts, "esxi-01")
    host_factory[
        "host"
    ].configManager.storageSystem.UpdateSoftwareInternetScsiEnabled.assert_called_once_with(
        enabled=False
    )


def test_iscsi_add_send_target(host_factory, opts):
    hba = _iscsi_hba()
    host_factory["host"] = _fake_host(iscsi_hba=hba)
    vim_host_security.iscsi_add_send_target(opts, "esxi-01", "10.0.0.50")
    call = host_factory["host"].configManager.storageSystem.AddInternetScsiSendTargets.call_args
    assert call.kwargs["iScsiHbaDevice"] == "vmhba33"
    assert call.kwargs["targets"][0].address == "10.0.0.50"
    assert call.kwargs["targets"][0].port == 3260


def test_iscsi_add_send_target_requires_hba(host_factory, opts):
    with pytest.raises(LookupError, match="software iSCSI initiator not enabled"):
        vim_host_security.iscsi_add_send_target(opts, "esxi-01", "10.0.0.50")


def test_iscsi_remove_send_target(host_factory, opts):
    hba = _iscsi_hba()
    host_factory["host"] = _fake_host(iscsi_hba=hba)
    vim_host_security.iscsi_remove_send_target(opts, "esxi-01", "10.0.0.50")
    call = host_factory["host"].configManager.storageSystem.RemoveInternetScsiSendTargets.call_args
    assert call.kwargs["targets"][0].address == "10.0.0.50"


def test_iscsi_set_chap(host_factory, opts):
    hba = _iscsi_hba()
    host_factory["host"] = _fake_host(iscsi_hba=hba)
    vim_host_security.iscsi_set_chap(
        opts, "esxi-01", name="chap-user", password="secret", direction="required"
    )
    call = host_factory[
        "host"
    ].configManager.storageSystem.UpdateInternetScsiAuthenticationProperties.call_args
    auth = call.kwargs["authenticationProperties"]
    assert auth.chapName == "chap-user"
    assert auth.chapSecret == "secret"
    assert auth.chapAuthEnabled is True
