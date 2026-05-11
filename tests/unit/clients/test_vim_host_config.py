"""Tests for clients.vim_host_config (managed-ESXi host config via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_host_config


def _service(key, running=False, policy="off"):
    s = MagicMock()
    s.key = key
    s.label = key
    s.running = running
    s.policy = policy
    s.required = False
    s.uninstallable = True
    return s


def _fake_host(
    ntp_servers=None,
    services=None,
    ad_info=None,
    advanced_options=None,
):
    h = MagicMock()
    h.config.dateTimeInfo.ntpConfig.server = ntp_servers or []
    h.config.service.service = services or []
    if ad_info is not None:
        h.config.authenticationManagerInfo.authConfig = [ad_info]
    else:
        h.config.authenticationManagerInfo = None
    # Advanced options
    if advanced_options is not None:
        h.configManager.advancedOption.setting = [
            MagicMock(key=k, value=v) for k, v in advanced_options.items()
        ]
        h.configManager.advancedOption.QueryOptions.side_effect = lambda name: (
            [MagicMock(key=name, value=advanced_options[name])] if name in advanced_options else []
        )
    h.configManager.dateTimeSystem = MagicMock()
    h.configManager.serviceSystem = MagicMock()
    h.configManager.authenticationManager.JoinDomain_Task.return_value = MagicMock(_moId="task-1")
    h.configManager.authenticationManager.LeaveCurrentDomain_Task.return_value = MagicMock(
        _moId="task-2"
    )
    return h


@pytest.fixture
def host_factory(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(vim_host_config, "_host", lambda opts, h, profile=None: holder["host"])
    return holder


# ---------- NTP ----------


def test_ntp_get_returns_servers_and_service_state(host_factory, opts):
    host_factory["host"] = _fake_host(
        ntp_servers=["time1.example.com", "time2.example.com"],
        services=[_service("ntpd", running=True, policy="on")],
    )
    result = vim_host_config.ntp_get(opts, "esxi-01")
    assert result == {
        "servers": ["time1.example.com", "time2.example.com"],
        "enabled": True,
        "policy": "on",
    }


def test_ntp_get_with_no_ntpd_service(host_factory, opts):
    host_factory["host"] = _fake_host(ntp_servers=["t.example.com"], services=[])
    result = vim_host_config.ntp_get(opts, "esxi-01")
    assert result["servers"] == ["t.example.com"]
    assert result["enabled"] is False
    assert result["policy"] == "off"


def test_ntp_set_servers_calls_update(host_factory, opts):
    vim_host_config.ntp_set_servers(opts, "esxi-01", ["time.example.com"])
    update_call = host_factory["host"].configManager.dateTimeSystem.UpdateDateTimeConfig
    update_call.assert_called_once()
    spec = update_call.call_args.kwargs["config"]
    assert spec.ntpConfig.server == ["time.example.com"]


def test_ntp_set_running_true_starts(host_factory, opts):
    vim_host_config.ntp_set_running(opts, "esxi-01", True)
    host_factory["host"].configManager.serviceSystem.StartService.assert_called_once_with(id="ntpd")


def test_ntp_set_running_false_stops(host_factory, opts):
    vim_host_config.ntp_set_running(opts, "esxi-01", False)
    host_factory["host"].configManager.serviceSystem.StopService.assert_called_once_with(id="ntpd")


def test_ntp_set_policy(host_factory, opts):
    vim_host_config.ntp_set_policy(opts, "esxi-01", "on")
    host_factory["host"].configManager.serviceSystem.UpdateServicePolicy.assert_called_once_with(
        id="ntpd", policy="on"
    )


# ---------- Services ----------


def test_service_list(host_factory, opts):
    host_factory["host"] = _fake_host(
        services=[
            _service("ntpd", running=True, policy="on"),
            _service("TSM-SSH", running=False, policy="off"),
        ]
    )
    result = vim_host_config.service_list(opts, "esxi-01")
    by_key = {s["key"]: s for s in result}
    assert by_key["ntpd"]["running"] is True
    assert by_key["TSM-SSH"]["policy"] == "off"


def test_service_start_stop_restart(host_factory, opts):
    vim_host_config.service_start(opts, "esxi-01", "TSM-SSH")
    vim_host_config.service_stop(opts, "esxi-01", "TSM-SSH")
    vim_host_config.service_restart(opts, "esxi-01", "ntpd")
    svc = host_factory["host"].configManager.serviceSystem
    svc.StartService.assert_called_with(id="TSM-SSH")
    svc.StopService.assert_called_with(id="TSM-SSH")
    svc.RestartService.assert_called_with(id="ntpd")


def test_service_set_policy(host_factory, opts):
    vim_host_config.service_set_policy(opts, "esxi-01", "TSM-SSH", "automatic")
    host_factory["host"].configManager.serviceSystem.UpdateServicePolicy.assert_called_once_with(
        id="TSM-SSH", policy="automatic"
    )


# ---------- Active Directory ----------


def test_ad_status_not_joined_when_no_auth_info(host_factory, opts):
    result = vim_host_config.ad_status(opts, "esxi-01")
    assert result == {"joined": False, "domain": None, "trust_status": None}


def test_ad_status_joined(host_factory, opts):
    ad = vim.host.ActiveDirectoryInfo()
    ad.enabled = True
    ad.joinedDomain = "example.com"
    host_factory["host"] = _fake_host(ad_info=ad)
    result = vim_host_config.ad_status(opts, "esxi-01")
    assert result["joined"] is True
    assert result["domain"] == "example.com"


def test_ad_join_passes_creds(host_factory, opts):
    vim_host_config.ad_join(opts, "esxi-01", "example.com", "admin", "secret")
    host_factory[
        "host"
    ].configManager.authenticationManager.JoinDomain_Task.assert_called_once_with(
        domainName="example.com", userName="admin", password="secret"
    )


def test_ad_leave(host_factory, opts):
    vim_host_config.ad_leave(opts, "esxi-01", force=True)
    host_factory[
        "host"
    ].configManager.authenticationManager.LeaveCurrentDomain_Task.assert_called_once_with(
        force=True
    )


# ---------- Advanced settings ----------


def test_advanced_get_single_key(host_factory, opts):
    host_factory["host"] = _fake_host(advanced_options={"UserVars.SuppressShellWarning": 1})
    result = vim_host_config.advanced_get(opts, "esxi-01", key="UserVars.SuppressShellWarning")
    assert result == 1


def test_advanced_get_missing_key_raises(host_factory, opts):
    host_factory["host"] = _fake_host(advanced_options={"X": 0})
    with pytest.raises(LookupError):
        vim_host_config.advanced_get(opts, "esxi-01", key="Y")


def test_advanced_get_full_dict(host_factory, opts):
    host_factory["host"] = _fake_host(advanced_options={"A": 1, "B": 2})
    result = vim_host_config.advanced_get(opts, "esxi-01")
    assert result == {"A": 1, "B": 2}


def test_advanced_set(host_factory, opts):
    vim_host_config.advanced_set(opts, "esxi-01", "UserVars.SuppressShellWarning", 1)
    update_call = host_factory["host"].configManager.advancedOption.UpdateOptions
    update_call.assert_called_once()
    changed = update_call.call_args.kwargs["changedValue"]
    assert len(changed) == 1
    assert changed[0].key == "UserVars.SuppressShellWarning"
    assert changed[0].value == 1
