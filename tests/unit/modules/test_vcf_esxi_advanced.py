"""Tests for modules.vcf_esxi_advanced."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_esxi_advanced as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def _opt(key, value):
    o = MagicMock()
    o.key = key
    o.value = value
    return o


def _fake_host(query_result=None):
    host = MagicMock()
    host.configManager.advancedOption.QueryOptions.return_value = query_result or []
    return host


def test_list():
    host = _fake_host(query_result=[_opt("Net.TcpipHeapMax", 512), _opt("Misc.Foo", "bar")])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.list_() == {"Net.TcpipHeapMax": 512, "Misc.Foo": "bar"}


def test_get():
    host = _fake_host(query_result=[_opt("Net.TcpipHeapMax", 512)])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.get("Net.TcpipHeapMax") == {"key": "Net.TcpipHeapMax", "value": 512}
    host.configManager.advancedOption.QueryOptions.assert_called_once_with(name="Net.TcpipHeapMax")


def test_set_value():
    host = _fake_host()
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.set_value("Net.TcpipHeapMax", 1024)
    assert result == {"key": "Net.TcpipHeapMax", "value": 1024}
    call = host.configManager.advancedOption.UpdateValues.call_args
    changed = list(call.kwargs["changedValue"])
    assert len(changed) == 1
    assert changed[0].key == "Net.TcpipHeapMax"
    assert changed[0].value == 1024
