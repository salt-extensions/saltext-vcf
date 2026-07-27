"""Tests for clients.esxi_auth_proxy (CAM / vSphere Authentication Proxy)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import esxi_auth_proxy as c


def _opt(key, value):
    o = MagicMock()
    o.key = key
    o.value = value
    return o


def _fake_host(advanced_options=None, ad_info=None):
    h = MagicMock()
    advanced_options = advanced_options or {}

    def _query(name):
        return [_opt(name, advanced_options[name])] if name in advanced_options else []

    h.configManager.advancedOption.QueryOptions.side_effect = _query
    if ad_info is None:
        h.configManager.authenticationManager.info = None
        h.config.authenticationManagerInfo = None
    else:
        info_obj = MagicMock()
        info_obj.authConfig = [ad_info]
        h.configManager.authenticationManager.info = info_obj
    h.configManager.authenticationManager.JoinDomainWithCAM_Task.return_value = MagicMock(
        _moId="task-join-1"
    )
    h.configManager.authenticationManager.LeaveCurrentDomain_Task.return_value = MagicMock(
        _moId="task-leave-1"
    )
    return h


@pytest.fixture
def host_holder(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(
        "saltext.vcf.utils.vim.resolve_host_system",
        lambda opts, name, profile=None: holder["host"],
    )
    return holder


def test_get_config_defaults_when_no_settings(host_holder, opts):
    result = c.get_config(opts, "esxi-01")
    assert result == {
        "cam_address": None,
        "verify_cam_cert": None,
        "joined": False,
        "domain": None,
    }


def test_get_config_reads_advanced_settings(host_holder, opts):
    host_holder["host"] = _fake_host(
        advanced_options={
            c.CAM_ADDRESS_KEY: "cam.example.com",
            c.CAM_VERIFY_KEY: 1,
        }
    )
    result = c.get_config(opts, "esxi-01")
    assert result["cam_address"] == "cam.example.com"
    assert result["verify_cam_cert"] is True


def test_get_config_verify_zero_is_false(host_holder, opts):
    host_holder["host"] = _fake_host(advanced_options={c.CAM_VERIFY_KEY: 0})
    assert c.get_config(opts, "esxi-01")["verify_cam_cert"] is False


def test_get_config_reports_ad_join(host_holder, opts):
    ad = vim.host.ActiveDirectoryInfo()
    ad.enabled = True
    ad.joinedDomain = "corp.example.com"
    host_holder["host"] = _fake_host(ad_info=ad)
    result = c.get_config(opts, "esxi-01")
    assert result["joined"] is True
    assert result["domain"] == "corp.example.com"


def test_set_config_writes_both_settings(host_holder, opts):
    c.set_config(opts, "esxi-01", cam_address="cam.example.com", verify_cam_cert=True)
    calls = host_holder["host"].configManager.advancedOption.UpdateValues.call_args_list
    # Two mutating writes = two calls, one per key
    keys_written = []
    for call in calls:
        changed = list(call.kwargs["changedValue"])
        assert len(changed) == 1
        keys_written.append((changed[0].key, changed[0].value))
    assert (c.CAM_ADDRESS_KEY, "cam.example.com") in keys_written
    assert (c.CAM_VERIFY_KEY, 1) in keys_written


def test_set_config_verify_false_stored_as_zero(host_holder, opts):
    c.set_config(opts, "esxi-01", verify_cam_cert=False)
    call = host_holder["host"].configManager.advancedOption.UpdateValues.call_args
    changed = list(call.kwargs["changedValue"])
    assert changed[0].key == c.CAM_VERIFY_KEY
    assert changed[0].value == 0


def test_set_config_skips_none(host_holder, opts):
    # Only cam_address given -> only one write
    c.set_config(opts, "esxi-01", cam_address="cam.example.com")
    assert host_holder["host"].configManager.advancedOption.UpdateValues.call_count == 1


def test_join_domain_via_cam(host_holder, opts):
    task_id = c.join_domain_via_cam(opts, "esxi-01", "corp.example.com", "cam.example.com")
    host_holder[
        "host"
    ].configManager.authenticationManager.JoinDomainWithCAM_Task.assert_called_once_with(
        domainName="corp.example.com", camServer="cam.example.com"
    )
    assert task_id == "task-join-1"


def test_leave_domain(host_holder, opts):
    task_id = c.leave_domain(opts, "esxi-01", force=True)
    host_holder[
        "host"
    ].configManager.authenticationManager.LeaveCurrentDomain_Task.assert_called_once_with(
        force=True
    )
    assert task_id == "task-leave-1"


def test_leave_domain_defaults_force_false(host_holder, opts):
    c.leave_domain(opts, "esxi-01")
    host_holder[
        "host"
    ].configManager.authenticationManager.LeaveCurrentDomain_Task.assert_called_once_with(
        force=False
    )
