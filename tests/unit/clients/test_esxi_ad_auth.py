"""Tests for clients.esxi_ad_auth (native ESXi AD join)."""

import http.client
from unittest.mock import MagicMock
from unittest.mock import PropertyMock

import pytest

from saltext.vcf.clients import esxi_ad_auth as c


def _fake_host(info=None, info_exc=None):
    h = MagicMock()
    mgr = h.configManager.activeDirectoryAuthentication
    if info_exc is not None:
        type(mgr).info = PropertyMock(side_effect=info_exc)
    else:
        mgr.info = info
    mgr.JoinDomain_Task.return_value = MagicMock(_moId="task-join-1")
    mgr.LeaveCurrentDomain_Task.return_value = MagicMock(_moId="task-leave-1")
    return h


def _fake_info(
    joined_domain=None,
    trusted=(),
    membership_status=None,
    smb_file_shares=None,
):
    info = MagicMock()
    info.joinedDomain = joined_domain
    info.trustedDomain = list(trusted)
    info.domainMembershipStatus = membership_status
    info.smbFileShares = smb_file_shares
    return info


@pytest.fixture
def host_holder(monkeypatch):
    holder = {"host": _fake_host()}
    monkeypatch.setattr(
        "saltext.vcf.utils.vim.resolve_host_system",
        lambda opts, name, profile=None: holder["host"],
    )
    return holder


def test_get_ad_state_when_info_is_none(host_holder, opts):
    result = c.get_ad_state(opts, "esxi-01")
    assert result == {
        "joined": False,
        "domain": None,
        "trusted_domains": [],
        "membership_status": None,
        "smb_file_shares": None,
    }


def test_get_ad_state_when_info_raises_http_503(host_holder, opts):
    # Never-joined hosts sometimes 503 on ``.info`` — treat as not-joined.
    host_holder["host"] = _fake_host(info_exc=http.client.HTTPException("503 Service Unavailable"))
    result = c.get_ad_state(opts, "esxi-01")
    assert result["joined"] is False
    assert result["domain"] is None


def test_get_ad_state_when_info_raises_connection_error(host_holder, opts):
    host_holder["host"] = _fake_host(info_exc=ConnectionError("boom"))
    result = c.get_ad_state(opts, "esxi-01")
    assert result["joined"] is False


def test_get_ad_state_reports_join(host_holder, opts):
    host_holder["host"] = _fake_host(
        info=_fake_info(
            joined_domain="corp.example.com",
            trusted=["corp.example.com", "other.example.com"],
            membership_status="ok",
            smb_file_shares=None,
        )
    )
    result = c.get_ad_state(opts, "esxi-01")
    assert result["joined"] is True
    assert result["domain"] == "corp.example.com"
    assert result["trusted_domains"] == ["corp.example.com", "other.example.com"]
    assert result["membership_status"] == "ok"


def test_get_ad_state_empty_joined_domain_is_not_joined(host_holder, opts):
    host_holder["host"] = _fake_host(info=_fake_info(joined_domain=""))
    result = c.get_ad_state(opts, "esxi-01")
    assert result["joined"] is False
    assert result["domain"] is None


def test_join_domain_calls_task(host_holder, opts):
    task_id = c.join_domain(opts, "esxi-01", "corp.example.com", "svc-esx-join", "S3cret!")
    host_holder[
        "host"
    ].configManager.activeDirectoryAuthentication.JoinDomain_Task.assert_called_once_with(
        domainName="corp.example.com", userName="svc-esx-join", password="S3cret!"
    )
    assert task_id == "task-join-1"


def test_leave_domain_default_force_false(host_holder, opts):
    task_id = c.leave_domain(opts, "esxi-01")
    host_holder[
        "host"
    ].configManager.activeDirectoryAuthentication.LeaveCurrentDomain_Task.assert_called_once_with(
        force=False
    )
    assert task_id == "task-leave-1"


def test_leave_domain_force_true(host_holder, opts):
    c.leave_domain(opts, "esxi-01", force=True)
    host_holder[
        "host"
    ].configManager.activeDirectoryAuthentication.LeaveCurrentDomain_Task.assert_called_once_with(
        force=True
    )
