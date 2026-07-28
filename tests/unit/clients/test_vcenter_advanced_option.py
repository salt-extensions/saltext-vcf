"""Tests for clients.vcenter_advanced_option (vCenter Server OptionManager via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vcenter_advanced_option


@pytest.fixture
def option_mgr(monkeypatch):
    mgr = MagicMock()
    fake_content = MagicMock(setting=mgr)
    monkeypatch.setattr(
        vcenter_advanced_option.soap, "content", lambda opts, profile=None: fake_content
    )
    return mgr


def _opt(key, value):
    return vim.option.OptionValue(key=key, value=value)


def test_advanced_get_single_key(opts, option_mgr):
    option_mgr.QueryOptions.return_value = [_opt("config.vpxd.stats.maxQueryMetrics", 64)]
    assert (
        vcenter_advanced_option.advanced_get(opts, key="config.vpxd.stats.maxQueryMetrics") == 64
    )


def test_advanced_get_all(opts, option_mgr):
    option_mgr.setting = [_opt("a", 1), _opt("b", 2)]
    assert vcenter_advanced_option.advanced_get(opts) == {"a": 1, "b": 2}


def test_advanced_get_empty_result_returns_none(opts, option_mgr):
    option_mgr.QueryOptions.return_value = []
    assert vcenter_advanced_option.advanced_get(opts, key="missing.key") is None


def test_advanced_get_invalid_name_fault_returns_none(opts, option_mgr):
    """vCenter raises ``vim.fault.InvalidName`` for a key it's never seen before.

    That's normal for an option that's never been set — not an error — since
    ``advanced_set`` can still create it, matching the reference Ansible
    module's behavior (``vmware_vcenter_advanced_option``).
    """
    option_mgr.QueryOptions.side_effect = vim.fault.InvalidName(
        name="config.vpxd.stats.maxQueryMetrics"
    )
    result = vcenter_advanced_option.advanced_get(opts, key="config.vpxd.stats.maxQueryMetrics")
    assert result is None


def test_advanced_set(opts, option_mgr):
    vcenter_advanced_option.advanced_set(opts, "config.vpxd.stats.maxQueryMetrics", 64)
    changed = option_mgr.UpdateOptions.call_args.kwargs["changedValue"]
    assert changed[0].key == "config.vpxd.stats.maxQueryMetrics"
    assert changed[0].value == 64
