"""Tests for modules.vcf_esxi_syslog."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_esxi_syslog as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def _opt(value):
    o = MagicMock()
    o.value = value
    return o


def _fake_host(*, log_host="udp://collector:514", log_level="info"):
    host = MagicMock()

    def query_options(name):
        if name == "Syslog.global.logHost":
            return [_opt(log_host)] if log_host is not None else []
        if name == "Syslog.global.logLevel":
            return [_opt(log_level)] if log_level is not None else []
        return []

    host.configManager.advancedOption.QueryOptions.side_effect = query_options
    return host


def test_get():
    host = _fake_host(log_host="udp://collector:514", log_level="info")
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.get()
    assert result["log_level"] == "INFO"
    assert result["servers"] == ["udp://collector:514"]


def test_set_servers():
    host = _fake_host(log_host="udp://collector:514")
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_servers(["udp://collector:514"])
    call = host.configManager.advancedOption.UpdateValues.call_args
    changed = list(call.kwargs["changedValue"])
    assert len(changed) == 1
    assert changed[0].key == "Syslog.global.logHost"
    assert changed[0].value == "udp://collector:514"


def test_set_log_level():
    host = _fake_host(log_level="debug")
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_log_level("DEBUG")
    call = host.configManager.advancedOption.UpdateValues.call_args
    changed = list(call.kwargs["changedValue"])
    assert len(changed) == 1
    assert changed[0].key == "Syslog.global.logLevel"
    assert changed[0].value == "debug"
